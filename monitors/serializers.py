

from rest_framework import serializers
from .models import CheckResult, Incident, Monitor


class MonitorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Monitor

        fields = [
            "id",
            "name",
            "url",
            "interval",
            "is_active",
            "is_currently_up",
            "last_response_time_ms",
            "last_checked_at",
            "next_check_at",
            "created_at"
        ]

        read_only_fields = [
            "id",
            "created_at"
        ]


class CheckResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CheckResult
        fields = [
            "id",
            "status_code",
            "response_time_ms",
            "is_up",
            "error_message",
            "checked_at"
        ]


class IncidentSerializer(serializers.ModelSerializer):
    monitor_name = serializers.ReadOnlyField(source="monitor.name")

    class Meta:
        model = Incident
        fields = [
            "id",
            "monitor",
            "monitor_name",
            "started_at",
            "resolved_at",
            "is_resolved",
        ]
        read_only_fields = fields
