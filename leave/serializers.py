from datetime import datetime

from rest_framework import serializers
from rest_framework_simplejwt.state import User

from leave.models import Leave, LeaveType, LeavePolicy, EmployeeLeaveStructure, get_number_working_days


class LeaveListSerializer(serializers.ModelSerializer):
    leave_policy = serializers.StringRelatedField()
    relief = serializers.StringRelatedField()
    changed_by = serializers.StringRelatedField()
    employee = serializers.StringRelatedField()
    status = serializers.StringRelatedField()

    class Meta:
        model = Leave
        fields = '__all__'


class LeaveSerializer(serializers.ModelSerializer):
    leave_policy = serializers.PrimaryKeyRelatedField(queryset=LeavePolicy.objects.all())
    relief = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    changed_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    employee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Leave
        exclude = ('days_taken',)

    def create(self, validated_data):
        instance = Leave(**validated_data)
        employee = instance.employee
        emp_leave = EmployeeLeaveStructure(employee, instance.leave_policy)
        # read leave settings from configuration
        prev_balance = emp_leave.calculate_leave_days(1)

        days_taken = get_number_working_days(instance.start_date,
                                             instance.end_date)
        leave_balance = prev_balance - days_taken
        instance.days_taken = days_taken
        instance.leave_balance = leave_balance
        instance.submission_date = datetime.today()
        instance.save()
        return instance


class LeaveTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeaveType
        fields = ['id', 'name']


class LeavePolicySerializer(serializers.ModelSerializer):
    leave_type = serializers.StringRelatedField()

    class Meta:
        model = LeavePolicy
        fields = ['id', 'leave_type']


