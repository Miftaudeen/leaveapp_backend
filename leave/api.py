from datetime import datetime

from django.utils.decorators import method_decorator
from rest_framework import generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from leave.models import Leave, LeaveType, LeavePolicy
from leave.serializers import LeaveSerializer, LeaveTypeSerializer, LeavePolicySerializer, LeaveListSerializer


class LeaveList(generics.ListAPIView):
    serializer_class = LeaveListSerializer

    def get_queryset(self):
        return Leave.objects.select_related('leave_policy', 'relief', 'changed_by')


class LeaveCreate(generics.CreateAPIView):
    serializer_class = LeaveSerializer
    queryset = Leave.objects.all()


class LeaveTypeList(generics.ListAPIView):
    serializer_class = LeaveTypeSerializer
    queryset = LeaveType.objects.all()


class LeavePolicyList(generics.ListAPIView):
    serializer_class = LeavePolicySerializer
    queryset = LeavePolicy.objects.all()


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'middle_name': user.middle_name,
            'hire_date': user.hire_date,
            'email': user.email,
            'username': user.username,
        })
