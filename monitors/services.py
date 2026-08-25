from datetime import timedelta

import requests

from .models import CheckResult, Incident


FAILURE_THRESHOLD = 3
SUCCESS_THRESHOLD = 3
VALID_EVENTS = {"DOWN", "RECOVERED"}


def process_monitor(monitor):
    previous_state = monitor.is_currently_up
    result = check_monitor(monitor)
    check_result = create_check_result(monitor, result)
    update_monitor(monitor, check_result)
    event = create_incident(monitor, check_result, previous_state)
    email_alerts(monitor, event)


def check_monitor(monitor):
    try:
        response = requests.get(monitor.url, timeout=10)
        return {
            "status_code": response.status_code,
            "response_time_ms": int(response.elapsed.total_seconds() * 1000),
            "error_message": None,
            "is_up": 200 <= response.status_code < 400,
        }
    except requests.RequestException as error:
        return {
            "status_code": None,
            "response_time_ms": None,
            "error_message": str(error),
            "is_up": False,
        }


def create_check_result(monitor, result):
    return CheckResult.objects.create(monitor=monitor, **result)


def update_monitor(monitor, result):
    if result.is_up:
        monitor.consecutive_successes += 1
        monitor.consecutive_failures = 0
    else:
        monitor.consecutive_failures += 1
        monitor.consecutive_successes = 0

    if monitor.is_currently_up and monitor.consecutive_failures >= FAILURE_THRESHOLD:
        monitor.is_currently_up = False
        monitor.consecutive_failures = 0
    elif not monitor.is_currently_up and monitor.consecutive_successes >= SUCCESS_THRESHOLD:
        monitor.is_currently_up = True
        monitor.consecutive_successes = 0

    monitor.last_checked_at = result.checked_at
    monitor.next_check_at = result.checked_at + timedelta(seconds=monitor.interval)
    monitor.last_response_time_ms = result.response_time_ms
    monitor.save(
        update_fields=[
            "is_currently_up",
            "last_response_time_ms",
            "last_checked_at",
            "next_check_at",
            "consecutive_successes",
            "consecutive_failures",
        ]
    )


def create_incident(monitor, result, previous_state):
    incident = Incident.objects.filter(monitor=monitor, is_resolved=False).first()

    if previous_state and not monitor.is_currently_up:
        if incident is None:
            Incident.objects.create(monitor=monitor, started_at=result.checked_at)
        return "DOWN"

    if not previous_state and monitor.is_currently_up:
        if incident is not None:
            incident.resolved_at = result.checked_at
            incident.is_resolved = True
            incident.save(update_fields=["resolved_at", "is_resolved"])
        return "RECOVERED"

    return None


def email_alerts(monitor, event):
    if event in VALID_EVENTS:
        from .tasks import send_email

        send_email.delay(monitor.id, event)
