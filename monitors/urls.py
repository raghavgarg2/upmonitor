
from rest_framework.routers import DefaultRouter
from .views import IncidentViewSet, MonitorViewSet


router = DefaultRouter()

router.register(
    "monitors",
    MonitorViewSet,
    basename="monitor"
)

router.register(
    "incidents",
    IncidentViewSet,
    basename="incident"
)


urlpatterns = router.urls
