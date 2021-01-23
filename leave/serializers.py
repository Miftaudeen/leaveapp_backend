from datetime import datetime

from rest_framework import serializers

from employees.models import Employee
from leave.models import Leave, LeaveType, LeavePolicy, EmployeeLeaveStructure, get_number_working_days


class ChoiceField(serializers.ChoiceField):

    def to_representation(self, obj):
        if obj == '' and self.allow_blank:
            return obj
        return self._choices[obj]

    def to_internal_value(self, data):
        # To support inserts with the value
        if data == '' and self.allow_blank:
            return ''

        for key, val in self._choices.items():
            if val == data:
                return key
        self.fail('invalid_choice', input=data)


class LeaveListSerializer(serializers.ModelSerializer):
    leave_policy = serializers.StringRelatedField()
    relief = serializers.StringRelatedField()
    changed_by = serializers.StringRelatedField()
    employee = serializers.StringRelatedField()
    status = serializers.CharField(source='get_status_display')

    class Meta:
        model = Leave
        fields = '__all__'


class LeaveSerializer(serializers.ModelSerializer):
    leave_policy = serializers.PrimaryKeyRelatedField(queryset=LeavePolicy.objects.all())
    relief = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    changed_by = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())
    employee = serializers.PrimaryKeyRelatedField(queryset=Employee.objects.all())

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


