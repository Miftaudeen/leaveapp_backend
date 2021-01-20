from configstore.configs import get_config
from rest_framework import serializers

from employees.models import Employee
from leave.models import Leave, LeavePlan, LeaveType, LeavePolicy, EmployeeLeaveStructure, get_number_working_days


class LeaveSerializer(serializers.ModelSerializer):
    leave_policy = serializers.PrimaryKeyRelatedField(queryset=LeavePolicy.objects.all())
    relief = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    changed_by = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())

    class Meta:
        model = Leave
        exclude = ['batch']

    def create(self, validated_data):
        instance = Leave(**validated_data)
        employee = instance.employee
        emp_leave = EmployeeLeaveStructure(employee, instance.leave_policy)
        # read leave settings from configuration
        leave_config = get_config('leave_options')
        prev_balance = emp_leave.calculate_leave_days(leave_config.get('leave_period_start', 1))

        days_taken = get_number_working_days(instance.start_date,
                                             instance.end_date)
        leave_balance = prev_balance - days_taken
        instance.days_taken = days_taken
        instance.leave_balance = leave_balance
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


class LeavePlanSerializer(serializers.ModelSerializer):
    leave_type = serializers.PrimaryKeyRelatedField(queryset=LeaveType.objects.all())
    relief = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())

    class Meta:
        model = LeavePlan
        fields = '__all__'
