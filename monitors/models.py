from django.db import models
from django.contrib.auth.models import User


class Monitor(models.Model):

    owner = models.ForeignKey(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    url = models.URLField()
    interval = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    is_currently_up = models.BooleanField(default=True)
    last_response_time_ms = models.PositiveIntegerField(null=True,blank=True)
    last_checked_at = models.DateTimeField(null=True,blank=True)
    next_check_at = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    consecutive_successes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class CheckResult(models.Model):
    monitor = models.ForeignKey(Monitor,on_delete=models.CASCADE)
    status_code = models.PositiveIntegerField(null=True,blank=True)
    response_time_ms = models.PositiveIntegerField(null=True,blank=True)
    is_up = models.BooleanField()
    error_message = models.TextField(null=True,blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.monitor.name} - {self.checked_at}"


class Incident(models.Model):
    monitor = models.ForeignKey(Monitor,on_delete=models.CASCADE)
    started_at = models.DateTimeField()
    resolved_at = models.DateTimeField(null=True,blank=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.monitor.name} - {self.started_at}"
