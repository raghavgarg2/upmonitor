from django.db.models import Avg, Count, IntegerField
from django.db.models.functions import Cast
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .models import Incident, Monitor
from .serializers import CheckResultSerializer, IncidentSerializer, MonitorSerializer
from .tasks import process_monitor_task


class MonitorViewSet(ModelViewSet):
    serializer_class = MonitorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Monitor.objects.filter(owner=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        monitor = self.get_object()
        history = monitor.checkresult_set.order_by("-checked_at")
        serializer = CheckResultSerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        monitor = self.get_object()
        stats = monitor.checkresult_set.aggregate(
            total_checks=Count("id"),
            average_response_time=Avg("response_time_ms"),
            uptime_percentage=Avg(Cast("is_up", IntegerField())),
        )

        if stats["uptime_percentage"] is not None:
            stats["uptime_percentage"] = round(stats["uptime_percentage"] * 100, 2)

        return Response(stats)

    @action(detail=True, methods=["post"], url_path="check")
    def check(self, request, pk=None):
        monitor = self.get_object()
        process_monitor_task.delay(monitor.id)
        return Response({"message": "Monitor check queued successfully."})


class IncidentViewSet(ReadOnlyModelViewSet):
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Incident.objects.filter(monitor__owner=self.request.user).select_related(
            "monitor"
        )
        is_resolved = self.request.query_params.get("is_resolved")

        if is_resolved in {"true", "false"}:
            queryset = queryset.filter(is_resolved=is_resolved == "true")

        return queryset.order_by("-started_at")
