from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone

from .models import Monitor
from .services import process_monitor


@shared_task
def process_monitor_task(monitor_id):
    try:
        monitor = Monitor.objects.get(id=monitor_id)
    except Monitor.DoesNotExist:
        return

    process_monitor(monitor)


@shared_task
def check_due_monitors():
    monitors = Monitor.objects.filter(is_active=True).filter(
        Q(next_check_at__isnull=True) | Q(next_check_at__lte=timezone.now())
    )

    for monitor in monitors:
        process_monitor_task.delay(monitor.id)


@shared_task
def send_email(monitor_id, event):
    try:
        monitor = Monitor.objects.select_related("owner").get(id=monitor_id)
    except Monitor.DoesNotExist:
        return

    if not monitor.owner.email:
        return

    if event == "RECOVERED":
        subject = f"[Uptime Monitor] Monitor Recovered: {monitor.name}"
        message = (
            "Your monitor has recovered and is now UP.\n\n"
            f"Monitor: {monitor.name}\n"
            f"URL: {monitor.url}\n\n"
            f"Recovered at: {timezone.now()}\n\n"
            "The endpoint is responding successfully again.\n\n"
            "Uptime Monitor"
        )
    elif event == "DOWN":
        subject = f"[Uptime Monitor] Monitor Down: {monitor.name}"
        message = (
            "Your monitor has been detected as DOWN.\n\n"
            f"Monitor: {monitor.name}\n"
            f"URL: {monitor.url}\n\n"
            f"Detected at: {timezone.now()}\n\n"
            "Our monitoring system will continue checking the endpoint and "
            "notify you once it recovers.\n\n"
            "Uptime Monitor"
        )
    else:
        return

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[monitor.owner.email],
        fail_silently=False,
    )
