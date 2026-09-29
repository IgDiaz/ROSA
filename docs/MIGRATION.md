# Upgrading ROSA by CDT to 0.4

Project: **Robotics Operational Systems and Agave**, maintained by CDT at `https://github.com/IgDiaz/ROSA`. The Python distribution is `rosa-robotics-kit`; its import is `rosa`. This project is independent of NASA/JPL's `jpl-rosa`. Use a dedicated virtual environment so packages sharing the `rosa` import cannot overwrite one another. The [Quick Start](../README.md#quick-start) installs directly from this repository.

## Protocol and requirements

Context exports use schema 1.1, adding `received_at`, `sequence` and `timestamp_kind` to each fact. Update strict receivers to the published schema before upgrading the sender. Existing CLI names, import names and HTTP header names are retained.

SQLite databases migrate additively when opened. Back up a database before upgrading. Existing observations retain their value/time and are marked `timestamp_kind="received"`; a strict acquisition profile requires newly acquired evidence. Persisted profiles default to the old demo's values. Existing simulation history and idempotent results remain available.

`observed_at` rejects future and negative timestamps. Integrators synchronize acquisition clocks to the receiver's Unix time; ROS simulated clock epochs require an explicit clock mapping before ingestion. Sequence numbers are optional in `observe`, mandatory in the stamped telemetry contract. Replayed or decreasing numbers cannot refresh an existing fact from that source.
