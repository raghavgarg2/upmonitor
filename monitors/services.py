import requests


#  r = requests.head(monitor.url)
#     status_code = r.status_code
#     response_time_ms = r.elapsed.total_seconds() * 1000
#     is_up  = False
#     if(status_code == 200):
#         is_up = True
#     error_message = "something went wrong"

#     return {
        
#     }



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
    



    

