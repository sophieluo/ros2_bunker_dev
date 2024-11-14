import numpy as np
from sensor_msgs.msg import PointCloud2
from nav_msgs.msg import OccupancyGrid
import rclpy
from rclpy.node import Node
from sensor_msgs_py import point_cloud2

class SlamProcessor(Node):
    def __init__(self):
        super().__init__('slam_processor')
        
        # 地图参数
        self.map_resolution = 0.05  # 5cm per cell
        self.map_width = 1000      # 50m / 0.05
        self.map_height = 1000     # 50m / 0.05
        self.map_origin_x = -25.0  # meters
        self.map_origin_y = -25.0  # meters
        
        # 过滤参数
        self.min_distance = 1.0    # 最小距离阈值(米)
        self.max_height = 1.8      # 最大高度阈值(米)
        
        # 创建点云订阅和地图发布
        self.subscription = self.create_subscription(
            PointCloud2,
            '/lio_sam/mapping/cloud_registered',
            self.point_cloud_callback,
            10)
            
        self.map_publisher = self.create_publisher(
            OccupancyGrid,
            '/map',
            10)
            
        self.occupancy_grid = np.zeros((self.map_height, self.map_width), dtype=np.int8)
        
        
        # 修改动态物体过滤参数
        self.window_size = 10  # 滑动窗口大小
        self.required_observations = 2  # 需要在窗口内的最小观测次数
        self.decay_rate = 2  # 每次衰减的计数值
        
        # 使用环形缓冲区存储最近几帧的观测
        self.observation_buffer = np.zeros((self.window_size, self.map_height, self.map_width), dtype=bool)
        self.buffer_index = 0
        
        # 定时器改为更快的频率
        self.create_timer(1, self.maintain_map)  # 每0.1秒执行一次地图维护
        
        # 添加雷达最大范围参数
        self.lidar_max_range = 10.0  # 雷达最大探测范围(米)
    
    def filter_points(self, points):
        """过滤点云数据"""
        # 计算每个点到原点的距离
        distances = np.sqrt(points[:, 0]**2 + points[:, 1]**2)
        
        # 应用距离和高度过滤
        valid_points = points[
            (distances > self.min_distance) &  # 距离过滤
            (points[:, 2] < self.max_height)   # 高度过滤
        ]
        
        return valid_points
        
    def point_to_grid(self, x, y):
        """Convert point coordinates to grid indices"""
        grid_x = int((x - self.map_origin_x) / self.map_resolution)
        grid_y = int((y - self.map_origin_y) / self.map_resolution)
        return grid_x, grid_y
        
    def update_occupancy_grid(self, points):
        """更新占用栅格，使用滑动窗口方法"""
        filtered_points = self.filter_points(points)
        
        # 清除当前缓冲区帧
        self.observation_buffer[self.buffer_index] = False
        
        # 更新当前帧的观测
        for x, y, _ in filtered_points:
            grid_x, grid_y = self.point_to_grid(x, y)
            if 0 <= grid_x < self.map_width and 0 <= grid_y < self.map_height:
                self.observation_buffer[self.buffer_index, grid_y, grid_x] = True
        
        # 计算滑动窗口内的观测次数
        observation_sum = np.sum(self.observation_buffer, axis=0)
        
        # 更新占用栅格
        # 被连续观测到的点标记为障碍物
        obstacles = observation_sum >= self.required_observations
        self.occupancy_grid[obstacles] = 100
        
        # 没有被足够次数观测到的点标记为空闲
        free_space = observation_sum < self.required_observations
        self.occupancy_grid[free_space] = 0
        
        # 更新缓冲区索引
        self.buffer_index = (self.buffer_index + 1) % self.window_size
        
    def is_in_lidar_range(self, grid_x, grid_y):
        """判断栅格是否在当前雷达可见范围内"""
        # 转换回世界坐标
        world_x = grid_x * self.map_resolution + self.map_origin_x
        world_y = grid_y * self.map_resolution + self.map_origin_y
        
        # 计算到雷达原点的距离
        distance = np.sqrt(world_x**2 + world_y**2)
        return distance <= self.lidar_max_range

    def maintain_map(self):
        """维护地图，只清除雷达范围内未观测到的障碍物"""
        # 计算当前观测状态
        current_observations = np.sum(self.observation_buffer, axis=0)
        
        # 创建雷达范围掩码
        lidar_range_mask = np.zeros_like(self.occupancy_grid, dtype=bool)
        for i in range(self.map_height):
            for j in range(self.map_width):
                if self.is_in_lidar_range(j, i):
                    lidar_range_mask[i, j] = True
        
        # 只清除在雷达范围内且未被观测到的区域
        unobserved = (current_observations == 0) & lidar_range_mask
        self.occupancy_grid[unobserved] = 0
        
                
    def publish_map(self):
        """Publish occupancy grid map"""
        msg = OccupancyGrid()
        msg.header.frame_id = "map"
        msg.header.stamp = self.get_clock().now().to_msg()
        
        msg.info.resolution = self.map_resolution
        msg.info.width = self.map_width
        msg.info.height = self.map_height
        msg.info.origin.position.x = self.map_origin_x
        msg.info.origin.position.y = self.map_origin_y
        
        # Flatten the grid to 1D array
        msg.data = self.occupancy_grid.flatten().tolist()
        
        self.map_publisher.publish(msg)

    def point_cloud_callback(self, msg):
        """Process incoming point cloud and update map"""
        pc_points = []
        for p in point_cloud2.read_points(msg, field_names=("x", "y", "z"), skip_nans=True):
            pc_points.append([p[0], p[1], p[2]])
        
        points = np.array(pc_points)
        self.update_occupancy_grid(points)
        self.publish_map()
        
def main(args=None):
    rclpy.init(args=args)
    node = SlamProcessor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()