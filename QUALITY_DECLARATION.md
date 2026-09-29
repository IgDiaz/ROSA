# Quality declaration · ROSA 0.4

ROSA develops robustness through measurable experiments and published evidence. The structure below follows the concerns in [REP-2004](https://github.com/openrobotics/reps/blob/main/_posts/rep-2004.md). It records current practices and the next acceptance gate; it does not assign a ROS quality level or imply upstream certification.

| Concern | Current evidence | Next acceptance gate |
|---|---|---|
| Version and API | Version 0.4.0, documented public API and migration guide | Stable 1.0 API after independent adopter feedback |
| Change control | CI on pushes/PRs; contribution and review guidance | Independent review and enforced protected-branch requirements |
| Documentation | Quickstart, API, contracts, reproducible ROS experiment, troubleshooting | Third-party install without maintainer assistance |
| Regression tests | Context, policy, replay, concurrency and persistence scenarios | Extend tests with every new capability and failure mode |
| Coverage | Branch measurement; fail below 80%; uploaded report | Raise the floor as uncovered paths are exercised meaningfully |
| Static analysis | Ruff error rules E9/F63/F7/F82 | Broader rules and reviewed formatting policy |
| ROS interoperability | Jazzy container job with actual DDS and observer process | Second ROS distribution and a physical observation-only pilot |
| Performance | 500-iteration timing script and CI artifact | Same-machine baseline and explicit regression budget after repeated samples |
| Dependencies | Standard-library core; optional upstream ROS and Ollama adapters | Per-version external-adapter compatibility evidence |
| Security | Loopback console, source requirements, bounded model outputs, export signing | Authenticated ROS deployment exercise and private reporting workflow |

## Coverage scope

The report includes all modules under `rosa` except `__main__.py` and `ros2.py`. The first is CLI wiring; the second is exercised separately in the Jazzy integration job. The local HTTP console remains in the coverage denominator. A passing percentage demonstrates exercised code, not functional-safety certification. Read the tests and the integration results together.

## Compatibility policy

Patch releases preserve documented interfaces within 0.4.x. Minor releases before 1.0 may change interfaces with migration notes. Public interfaces are listed in `docs/API.md`; underscored methods are internal. JSON schemas carry their own version. Database changes in 0.4 are additive, and legacy acquisition provenance is conservatively labelled as reception time.

## Release evidence

A release candidate must pass the OS/Python matrix, coverage floor, static checks, schema checks, installed-wheel test and ROS integration job. Contributors add a scenario that demonstrates the behavior or failure they change. Real robot and model claims require results from the actual hardware/model configuration, recorded with its versions and operating assumptions.

## Relationship to ROS 2

Reuse upstream libraries through public interfaces. Keep their licenses and attribution. Reference upstream quality declarations, but assess ROSA's own orchestration, storage and policy behavior independently. Engineering maturity is built through repeated validation against specific industrial requirements.
