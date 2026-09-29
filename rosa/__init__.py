# SPDX-FileCopyrightText: 2026 CDT
# SPDX-License-Identifier: MIT
"""ROSA: an evolving context and command layer for robot applications."""
from .context import ContextStore, Scope
from .runtime import Runtime
from .profile import OperationalProfile
from .telemetry import ingest_telemetry

__all__ = ["ContextStore", "Scope", "Runtime", "OperationalProfile", "ingest_telemetry"]
__version__ = "0.4.0"
