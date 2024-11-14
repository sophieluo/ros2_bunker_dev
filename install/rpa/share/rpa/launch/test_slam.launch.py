# test_slam.launch.py
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('rpa')
    
    nav2_config = os.path.join(pkg_share, 'config', 'nav2_params.yaml')

    rviz_config_file = os.path.join(
        get_package_share_directory('rpa'),
        'config',
        'nav2.rviz'
    )
    
    return LaunchDescription([
        # SLAM processor
        Node(
            package='rpa',
            executable='slam_processor',
            name='slam_processor',
            output='screen'
        ),
        
        # Nav2 nodes
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen'
        ),
        
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            parameters=[nav2_config],
            output='screen'
        ),
        
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{'use_sim_time': False},
                       {'autostart': True},
                       {'node_names': ['map_server', 
                                     'amcl',
                                     'controller_server',
                                     'planner_server',
                                     'recoveries_server',
                                     'bt_navigator']}]
        ),
        
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            parameters=[nav2_config],
            output='screen'
        ),
        
        # RViz
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file],
            output='screen'
        )
    ])