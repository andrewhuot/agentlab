"""Notifications system for AutoAgent — webhooks, Slack, email alerts."""

from __future__ import annotations

from notifications.manager import NotificationManager, Subscription
from notifications.integration import (
    emit_deployment,
    emit_gate_failure,
    emit_health_drop,
    emit_new_opportunity,
    emit_optimization_complete,
    emit_safety_violation,
)
from notifications.scheduler import NotificationScheduler

__all__ = [
    "NotificationManager",
    "NotificationScheduler",
    "Subscription",
    "emit_deployment",
    "emit_gate_failure",
    "emit_health_drop",
    "emit_new_opportunity",
    "emit_optimization_complete",
    "emit_safety_violation",
]
