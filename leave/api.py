from datetime import datetime

from django.utils.decorators import method_decorator
from rest_framework import generics

from leave.models import Leave, LeaveType, LeavePolicy
from leave.serializers import LeaveSerializer, LeavePlanSerializer, LeaveTypeSerializer, LeavePolicySerializer
from leaveapp_backend.utils import cache_per_user


class LeaveList(generics.ListCreateAPIView):
    serializer_class = LeaveSerializer

    def get_queryset(self):
        user = self.request.user
        return Leave.objects.select_related('leave_policy', 'relief', 'changed_by').filter(employee=user)

    @method_decorator(cache_per_user(60 * 1))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class LeaveTypeList(generics.ListAPIView):
    serializer_class = LeaveTypeSerializer
    queryset = LeaveType.objects.all()


class LeavePolicyList(generics.ListAPIView):
    serializer_class = LeavePolicySerializer
    queryset = LeavePolicy.objects.all()
