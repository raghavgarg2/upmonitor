from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Monitor
from django.db.models.functions import Cast
from .serializers import MonitorSerializer,CheckResultSerializer
from django.db.models import (Count, Avg,Sum, Min, Max,IntegerField)
from .services import process_monitor



class MonitorViewSet(ModelViewSet):

    serializer_class = MonitorSerializer

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):
        return Monitor.objects.filter(
            owner=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save(
            owner=self.request.user
        )
    
    @action(detail=True,methods=["get"])
    def history(self,request,pk=None):
       
       monitor = self.get_object() 
       # we are not doing Monitor.objects.get(pk=pk) because it bypasses the authorization filter
       #this internally does something like
       #queryset = self.get_queryset()
       #monitor = get_object_or_404(
       #queryset,
       #pk=5
       #)

       history = monitor.checkresult_set.all()

       serializer = CheckResultSerializer(
           history,
           many = True
       )

       return Response(
           serializer.data
       )
    
    @action(methods=["get"],detail=True)
    def stats(self,request,pk=None):

        monitor = self.get_object()

        history = monitor.checkresult_set.all()

        stats = history.aggregate(
             total_checks=Count("id"),
             average_response_time=Avg("response_time_ms"),
             uptime_percentage=Avg(
               Cast("is_up", IntegerField())
              )
        )
        if stats["uptime_percentage"] is not None:
            stats["uptime_percentage"] = round(
                stats["uptime_percentage"] * 100,
                2
            )

        
        return Response(
            stats
        )
    
    @action(methods=["post"],detail=True)
    def monitorUrl(self,request,pk=None):
        monitor = self.get_object()

        process_monitor(monitor)

        return Response({
            "msg" : "monitor checked successfully"
        })
        

        


















# from rest_framework.permissions import (
#     AllowAny,
#     IsAuthenticated
# )

# class MonitorViewSet(ModelViewSet):

#     serializer_class = MonitorSerializer

#     def get_permissions(self):

#         if self.action in [
#             "list",
#             "retrieve"
#         ]:
#             return [AllowAny()]

#         return [IsAuthenticated()]







# # monitors/serializers.py

# from rest_framework import serializers
# from .models import Monitor


# class MonitorSerializer(serializers.ModelSerializer):

#     class Meta:
#         model = Monitor

#         fields = [
#             "id",
#             "name",
#             "url",
#             "interval",
#             "is_active",
#             "created_at"
#         ]

#         read_only_fields = [
#             "id",
#             "created_at"
#         ]



# class MonitorCreateAPIView(APIView):

#     permission_classes = [
#         IsAuthenticated
#     ]

#     def post(self, request):

#         serializer = MonitorSerializer(
#             data=request.data
#         )

#         serializer.is_valid(
#             raise_exception=True
#         )

#         serializer.save(
#             owner=request.user
#         )

#         return Response(
#             serializer.data,
#             status=status.HTTP_201_CREATED
#         )

