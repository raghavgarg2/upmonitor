

from celery import shared_task
from .models import Monitor
from .services import process_monitor
from django.utils import timezone
from django.core.mail import send_mail

@shared_task
def test_tast():
    print("hellle")


@shared_task
def process_monitor_task(monitor_id):
    monitor = Monitor.objects.get(
        id = monitor_id
    )
    process_monitor(monitor)

@shared_task
def check_due_monitors():
    monitors = Monitor.objects.filter(
        is_active = True,
        next_check_at__lte = timezone.now()
    )

    for monitor in monitors:
        process_monitor_task.delay(
            monitor.id
        )


@shared_task
def send_email(monitor_id,event):
    print("helleeeeeeeee")
    monitor = Monitor.objects.select_related("owner").get(id = monitor_id)
    if event == "RECOVERED":

        subject = (
          f"[Uptime Monitor] "
          f"Monitor Recovered: {monitor.name}"
    )

        message = (
          f"Your monitor has recovered and is now UP.\n\n"
          f"Monitor: {monitor.name}\n"
          f"URL: {monitor.url}\n\n"
          f"Recovered At: {timezone.now()}\n\n"
          f"The endpoint is responding "
          f"successfully again.\n\n"
          f"Uptime Monitor"
    )

    
    elif event == "DOWN":
        subject = (
          f"[Uptime Monitor] "
          f"Monitor Down: {monitor.name}"
    )

        message = (
          f"Your monitor has been detected as DOWN.\n\n"
          f"Monitor: {monitor.name}\n"
          f"URL: {monitor.url}\n\n"
          f"Detected At: {timezone.now()}\n\n"
          f"Our monitoring system will continue "
          f"checking the endpoint and notify "
          f"you once it recovers.\n\n"
          f"Uptime Monitor"
    )
    else:
        return 
        
    
    send_mail(
        subject=subject,
        message=message,
        from_email="alerts@uptimemonitor.com",
        recipient_list=[monitor.owner.email],
        fail_silently=False

    )
    




