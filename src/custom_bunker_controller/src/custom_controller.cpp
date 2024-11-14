#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"

class CustomController : public rclcpp::Node {
public:
    // CustomController() : Node("custom_controller") {
    //     publisher_ = this->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);
    //     //sends the message evry 500ms. if reduce this value to like 100ms, 
    //     //if send messages more frequently, thus the robot will appear to move smoother
    //     timer_ = this->create_wall_timer(
    //         500ms, std::bind(&CustomController::publish_velocity, this));
    // }

    // for smooth movement, need a loop
    CustomController() : Node("custom_controller") {
        publisher_ = this->create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);
        move_robot();  // Start moving the robot when the node runs
    }

private:
    // void publish_velocity() {
    //     auto msg = geometry_msgs::msg::Twist();
    //     msg.linear.x = 0.5;  // Set linear and angular values
    //     msg.angular.z = 0.1;
    //     publisher_->publish(msg);
    // }

    void move_robot() {
        auto msg = geometry_msgs::msg::Twist();
        msg.linear.x = 0.5;  // Constant forward speed at 0.5 m/s
        msg.angular.z = 0.0; // No turning

        // Keep publishing until manually stopped
        while (rclcpp::ok()) {
            publisher_->publish(msg);
            rclcpp::sleep_for(std::chrono::milliseconds(100));  // Small delay to keep commands continuous
        }
    }

    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr publisher_;
    // no need for timer if using a loop
    // rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char * argv[]) {
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<CustomController>());
    rclcpp::shutdown();
    return 0;
}