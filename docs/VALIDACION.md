# Validation evidence · ROSA / Minerva 0.4.0

The standard-library suite includes **43 tests**. It covers scoped memory, requirements, acquisition age, source constraints, replay handling, proposal invalidation, delayed interpretation, clock rollback, additive database migration and concurrent confirmation, alongside the original adapter and loopback-console scenarios.

```bash
python -m unittest discover -s tests -v
python -m pip install -e . -r requirements-dev.txt
python -m coverage run -m unittest discover -s tests
python -m coverage report
python -m ruff check .
python scripts/check_contracts.py
python scripts/benchmark.py
```

The coverage gate is 80% including branches; its exact scope is in `QUALITY_DECLARATION.md`. CI uploads coverage XML and a 500-iteration timing report. Timings describe one rules/SQLite simulation workload on the runner, not robot performance or improvement over ROS 2.

The OS matrix runs Linux, Windows and macOS with Python 3.11/3.12. A clean wheel check verifies imported package identity, bundled console assets and separation from the private website. A separate `ros:jazzy-ros-base` job starts the actual observer and exchanges DDS messages: timestamped context arrives, an obstacle updates it and a replay cannot clear that obstacle.

Current run results are published in [GitHub Actions](https://github.com/IgDiaz/ROSA/actions/workflows/tests.yml). Hardware actuation, actual model-specific accuracy, external receiver delivery, load and physical safety are separate experiment stages. Controlled Ollama and gateway responses test contracts; they are not results from a deployed model or third-party platform.
