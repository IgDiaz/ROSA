# SPDX-FileCopyrightText: 2026 CDT
# SPDX-License-Identifier: MIT
"""Optional ROS 2 observer. No actuator publisher is defined in this package.

Run with: python -m rosa.ros2 --db rosa-ros.sqlite3
Use a separate observer profile; do not mix simulator and physical telemetry.
"""
import argparse
import json
from .context import ContextStore, Scope


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="rosa-ros.sqlite3")
    parser.add_argument("--user", default="local")
    parser.add_argument("--robot", default="robot_01")
    args = parser.parse_args()
    try:
        import rclpy
        from rclpy.node import Node
        from rclpy.qos import qos_profile_sensor_data
        from sensor_msgs.msg import BatteryState
        from std_msgs.msg import Bool, String
    except ImportError as exc:
        raise SystemExit("Activa primero un entorno ROS 2 con rclpy, sensor_msgs y std_msgs.") from exc

    store, scope = ContextStore(args.db), Scope(args.user, args.robot)
    store.register(scope, mode="observation")
    if store.robot(scope)["mode"] != "observation":
        raise SystemExit("Este perfil está reservado para simulación. Usa otro robot o archivo DB.")
    rclpy.init()

    class Observer(Node):
        def __init__(self):
            super().__init__("rosa_observer", namespace=f"/rosa/{scope.user_id}/{scope.robot_id}")
            self.create_subscription(BatteryState, "battery", self.battery, qos_profile_sensor_data)
            self.create_subscription(Bool, "obstacle", lambda m: self.fact("obstacle", m.data), 10)
            self.create_subscription(Bool, "estop", lambda m: self.fact("estop", m.data), 10)
            self.create_subscription(String, "position", lambda m: self.fact("position", m.data), 10)
            self.context_publisher = self.create_publisher(String, "context", 10)
            self.create_timer(1.0, self.publish_context)

        def battery(self, message):
            # BatteryState percentage uses [0,1]; NaN / unknown values are rejected.
            self.fact("battery", message.percentage * 100)

        def fact(self, name, value):
            try:
                store.observe(scope, {name: value}, source=f"ros2/{name}")
            except ValueError as exc:
                self.get_logger().warning(str(exc))

        def publish_context(self):
            message = String()
            message.data = json.dumps(store.snapshot(scope), ensure_ascii=False)
            self.context_publisher.publish(message)

    node = Observer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        store.close()


if __name__ == "__main__":
    main()
