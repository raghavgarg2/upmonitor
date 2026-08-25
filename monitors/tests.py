from unittest.mock import patch

from django.contrib.auth.models import User
from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Incident, Monitor
from .services import process_monitor
from .tasks import send_email


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


class MonitorApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner")
        self.other_user = User.objects.create_user(username="other-user")
        self.monitor = Monitor.objects.create(
            owner=self.owner,
            name="API monitor",
            url="https://example.com",
            is_currently_up=False,
            last_response_time_ms=250,
            last_checked_at=timezone.now(),
        )
        self.owner_incident = Incident.objects.create(
            monitor=self.monitor,
            started_at=timezone.now(),
        )
        other_monitor = Monitor.objects.create(
            owner=self.other_user,
            name="Private monitor",
            url="https://example.org",
        )
        Incident.objects.create(monitor=other_monitor, started_at=timezone.now())

    def test_monitor_list_includes_current_status(self):
        self.client.force_authenticate(self.owner)

        response = self.client.get("/api/monitors/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        monitor = response.data[0]
        self.assertFalse(monitor["is_currently_up"])
        self.assertEqual(monitor["last_response_time_ms"], 250)
        self.assertIn("last_checked_at", monitor)

    def test_incidents_are_limited_to_the_authenticated_user(self):
        self.client.force_authenticate(self.owner)

        response = self.client.get("/api/incidents/?is_resolved=false")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.owner_incident.id)
        self.assertEqual(response.data[0]["monitor_name"], "API monitor")


class EmailTaskTests(TestCase):
    def setUp(self):
        owner = User.objects.create_user(
            username="email-owner",
            email="owner@example.com",
        )
        self.monitor = Monitor.objects.create(
            owner=owner,
            name="Email monitor",
            url="https://example.com",
        )

    @patch("monitors.tasks.send_mail")
    def test_down_alert_uses_the_configured_sender(self, mocked_send_mail):
        send_email.run(self.monitor.id, "DOWN")

        mocked_send_mail.assert_called_once()
        kwargs = mocked_send_mail.call_args.kwargs
        self.assertEqual(kwargs["from_email"], settings.DEFAULT_FROM_EMAIL)
        self.assertEqual(kwargs["recipient_list"], ["owner@example.com"])
        self.assertIn("Monitor Down", kwargs["subject"])
