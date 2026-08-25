from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from .models import Incident, Monitor
from .services import process_monitor


class MonitorLifecycleTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="monitor-owner")
        self.monitor = Monitor.objects.create(
            owner=self.owner,
            name="Example",
            url="https://example.com",
        )

    def process_result(self, is_up):
        with (
            patch(
                "monitors.services.check_monitor",
                return_value={
                    "status_code": 200 if is_up else 503,
                    "response_time_ms": 10,
                    "error_message": None if is_up else "Service unavailable",
                    "is_up": is_up,
                },
            ),
            patch("monitors.services.email_alerts") as email_alerts,
        ):
            process_monitor(self.monitor)
        self.monitor.refresh_from_db()
        return email_alerts

    def test_marks_down_and_recovers_after_three_consecutive_results(self):
        for _ in range(2):
            email_alerts = self.process_result(is_up=False)
            self.assertTrue(self.monitor.is_currently_up)
            self.assertEqual(Incident.objects.count(), 0)
            email_alerts.assert_called_once_with(self.monitor, None)

        email_alerts = self.process_result(is_up=False)
        self.assertFalse(self.monitor.is_currently_up)
        self.assertEqual(self.monitor.consecutive_failures, 0)
        incident = Incident.objects.get(monitor=self.monitor)
        self.assertFalse(incident.is_resolved)
        email_alerts.assert_called_once_with(self.monitor, "DOWN")

        for _ in range(2):
            email_alerts = self.process_result(is_up=True)
            self.assertFalse(self.monitor.is_currently_up)
            email_alerts.assert_called_once_with(self.monitor, None)

        email_alerts = self.process_result(is_up=True)
        self.assertTrue(self.monitor.is_currently_up)
        self.assertEqual(self.monitor.consecutive_successes, 0)
        incident.refresh_from_db()
        self.assertTrue(incident.is_resolved)
        self.assertIsNotNone(incident.resolved_at)
        email_alerts.assert_called_once_with(self.monitor, "RECOVERED")
