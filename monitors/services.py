import requests
from .models import CheckResult,Monitor,Incident
from datetime import timedelta

def process_monitor(monitor):
    result = check_monitor(monitor)

    check_result = create_check_result(
        monitor,
        result
    )

    update_monitor(
        monitor,
        check_result
    )

    create_incident(
        monitor,
        check_result
    )




def check_monitor(monitor):
    try:
        response = requests.get(
            monitor.url,
            timeout=10
        )

        status_code = response.status_code

        response_time_ms = int(
            response.elapsed.total_seconds() * 1000
        )

        is_up = (
            200 <= status_code < 400
        )

        return {
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "error_message": None,
            "is_up": is_up,
        }

    except requests.RequestException as e:
        return {
            "status_code": None,
            "response_time_ms": None,
            "error_message": str(e),
            "is_up": False,
        }
    

def create_check_result(monitor,result):
    return CheckResult.objects.create(
        monitor = monitor,
        **result
    )

def update_monitor(monitor,result):
    monitor.is_currently_up = result.is_up
    monitor.last_checked_at = result.checked_at
    monitor.next_check_at = result.checked_at +  timedelta(seconds = monitor.interval)
    monitor.last_response_time_ms = result.response_time_ms

    monitor.save(update_fields = ["is_currently_up","last_response_time_ms","last_checked_at","next_check_at"])



def create_incident(monitor,result):
    # incident = Incident.objects.get( // we are not using this because get throws excepion
    #         monitor = monitor,
    #         is_resolved = False
    #     )
    incident = Incident.objects.filter(
        monitor=monitor,
        is_resolved=False
    ).first()

    if not monitor.is_currently_up:
        if incident is None:
            Incident.objects.create(
                monitor = monitor,
                started_at = result.checked_at
            )
    

    else:
        if(incident is not None):
           incident.resolved_at = result.checked_at
           incident.is_resolved = True
           incident.save(update_fields=["resolved_at","is_resolved"])

    
