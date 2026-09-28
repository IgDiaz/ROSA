# Security

This is an experimental simulator and integration toolkit, not a control or functional-safety system.

Do not post credentials, private telemetry or live-service exploit details in public issues. Use GitHub private vulnerability reporting if enabled. Otherwise, request a private contact in an issue without including sensitive details.

Keep the local console on loopback. Python scopes and ROS namespaces do not authenticate callers.

Production robotics requires source authentication, acquisition timestamps, bounded actions, watchdogs, risk assessment and an independent physical emergency stop. Do not connect simulation methods directly to actuators. No response-time commitment or formal security support policy is offered for this initial release.

See [PRIVACY.md](PRIVACY.md) for local storage and optional data transfers. Review examples and exported logs before sharing them.
