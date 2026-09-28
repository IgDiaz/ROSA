# Validation — ROSA / Minerva 0.3.1

The independent SDK retains 22 tests for scoped context, persistence,
proposal expiration, stale evidence, idempotent simulation, optional-adapter
contracts, and the loopback HTTP console. Run:

```bash
python -m unittest discover -s tests -v
```

The distribution check builds and installs the wheel outside the checkout,
verifies the local console/icon are present, and rejects website landing/server
files. CI runs core tests on Linux, Windows and macOS with Python 3.11/3.12,
and a separate package check on Linux. Consult Actions for current results.

The website's session isolation and hosting tests belong to its separate
application repository and are not SDK validation claims.

Not validated: physical robot control, a real ROS 2 deployment, a real Ollama
model, an external agent receiver, production load, functional safety or
performance improvements over another platform. Adapter tests use controlled
responses. SQLite event history has no automatic retention policy.
