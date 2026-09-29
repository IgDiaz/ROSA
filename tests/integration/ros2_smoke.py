"""Exercise the real ROS 2 Jazzy graph, observer process and stamped telemetry.

Run in a sourced ROS environment: python3 tests/integration/ros2_smoke.py
Uses synthetic observations and never publishes actuator commands.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

import rclpy
from std_msgs.msg import String


def main():
    rclpy.init()
    node = rclpy.create_node("rosa_integration_probe")
    received = []
    node.create_subscription(String, "/rosa/ci/amr/context",
                             lambda m: received.append(json.loads(m.data)), 10)
    publisher = node.create_publisher(String, "/rosa/ci/amr/telemetry", 10)
    with tempfile.TemporaryDirectory() as directory:
        profile = Path(directory) / "profile.json"
        profile.write_text(json.dumps({"require_acquisition_time": True,
                                       "allowed_sources": ["ros2/telemetry"]}))
        process = subprocess.Popen([sys.executable, "-m", "rosa.ros2", "--db",
                                    directory + "/context.db", "--user", "ci", "--robot", "amr",
                                    "--profile", str(profile)], stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, env=os.environ.copy())
        def deliver(sequence, obstacle, expected_sequence, expected_obstacle):
            deadline = time.monotonic() + 20
            received.clear()
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise AssertionError("Observer exited: " + process.stdout.read())
                packet = {"schema_version": "1.0", "user_id": "ci", "robot_id": "amr",
                          "sequence": sequence, "observed_at": time.time(),
                          "values": {"battery": 82, "obstacle": obstacle, "estop": False, "position": "base"}}
                publisher.publish(String(data=json.dumps(packet)))
                rclpy.spin_once(node, timeout_sec=.1)
                for snapshot in received:
                    fact = snapshot.get("facts", {}).get("obstacle", {})
                    if fact.get("sequence") == expected_sequence and fact.get("value") is expected_obstacle:
                        assert snapshot["mode"] == "observation"
                        assert fact["timestamp_kind"] == "acquired"
                        return snapshot
            raise AssertionError("Expected context was not received from the ROS graph")
        try:
            deliver(1, False, 1, False)
            deliver(2, True, 2, True)
            deliver(1, False, 2, True)  # old packet must not erase the obstacle
            print("ROS 2 Jazzy: live DDS observation, acquisition time and replay rejection passed")
        finally:
            process.terminate()
            try: process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill();process.communicate()
            node.destroy_node()
            rclpy.shutdown()


if __name__ == "__main__":
    main()
