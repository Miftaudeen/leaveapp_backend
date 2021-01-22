from datetime import datetime

from rest_framework import serializers
from rest_framework_simplejwt.state import User

from employees.models import Employee
from leave.models import Leave, LeaveType, LeavePolicy, EmployeeLeaveStructure, get_number_working_days


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        exclude = ('password',)

