

from rest_framework import serializers
from .models import Monitor,CheckResult


class MonitorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Monitor

        fields = [
            "id",
            "name",
            "url",
            "interval",
            "is_active",
            "created_at"
        ]

        read_only_fields = [
            "id",
            "created_at"
        ]


class CheckResultSerializer(serializers.ModelSerializer):
    class Meta : 
        model = CheckResult
        fields = [
            "id",
            "status_code",
            "response_time_ms",
            "is_up",
            "error_message",
            "checked_at"
        ]