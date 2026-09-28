# Third-party licenses and provenance

ROSA's original implementation is copyright (c) 2026 CDT and is licensed under
the MIT terms in [LICENSE](LICENSE). The additional [LICENSE-CDT](LICENSE-CDT)
records CDT's grant for those contributions. Neither file replaces or changes
third-party ownership, licenses or notices.

## ROS and ROS 2

ROS inspired this project's modular approach. The optional adapter in
`rosa/ros2.py` imports an existing ROS 2 installation. This repository does not
vendor ROS or ROS 2 source code or binaries. Inspiration and interoperability do not transfer upstream copyrights to
CDT or relicense upstream software under MIT.

ROS and ROS 2 comprise separately licensed packages. The classic ROS core uses
BSD licensing, while other packages use their own terms; see the
[official ROS license overview](https://osrf.github.io/www.ros.org/).

The directly imported ROS 2 components identify their licenses as follows
(upstream references checked on 2026-09-28):

| Component | License | Upstream reference |
|---|---|---|
| `rclpy` | Apache License 2.0 | [LICENSE](https://github.com/ros2/rclpy/blob/rolling/LICENSE) |
| `sensor_msgs` | Apache License 2.0 | [package.xml](https://github.com/ros2/common_interfaces/blob/rolling/sensor_msgs/package.xml) |
| `std_msgs` | Apache License 2.0 | [package.xml](https://github.com/ros2/common_interfaces/blob/rolling/std_msgs/package.xml) |

The installed version's license files remain authoritative. When distributing
third-party components or incorporating any of their code, preserve the
applicable license text, copyright notices, attribution and any required NOTICE
files. Mark modifications when required by that component's license. Do not
replace upstream author credits with CDT.

## Other dependencies and models

The SDK uses Python's standard library and declares no external runtime
dependencies. Python and optional packages installed by the integrator retain
their own licenses and notices. The public website's dependencies and hosting
configuration are maintained separately and are not distributed with this SDK.

The optional local AI adapter calls a separately installed Ollama service. This
repository does not bundle Ollama or model weights. Each installed model's terms
must be checked independently; CDT's MIT grant does not cover those weights.

This document describes provenance and direct integration points, not an
exhaustive inventory of transitive dependencies. No affiliation with or
endorsement by ROS, Open Robotics or Ollama is implied.
