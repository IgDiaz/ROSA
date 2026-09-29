# Contributing

Start with a small reproducible scenario: version, OS, Python version, exact command and expected/observed behavior. Use synthetic data and remove credentials/private telemetry.

```bash
python -m venv .venv
# Activate the environment for your OS, then:
python -m pip install -e .
python -m unittest discover -s tests -v
```

The core and its tests have no runtime dependencies. Website deployment and hosted-service tests are maintained separately. Keep web frameworks and ROS out of the core. Use adapters rather than generated executable code. Preserve scope, freshness, explicit confirmation and idempotency.

Comment design reasons and invariants. Update schemas and examples when contracts change. Add meaningful tests for new behavior, and check desktop/mobile and keyboard access for UI changes. State which tests were run and which still need hardware.

Open focused pull requests describing the problem, changed behavior and validation. Contributions use this project's MIT license. Disclose substantial AI assistance and review generated code independently. Do not claim safety, accuracy or performance improvements without measurements.

Quality changes follow [QUALITY_DECLARATION.md](QUALITY_DECLARATION.md). Run the development-tool checks there and include the relevant evidence in a PR. New operating requirements need delayed, stale, replay and profile-change scenarios when applicable.
