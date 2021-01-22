from rest_framework import generics

from employees.models import Employee
from employees.serializers import EmployeeSerializer


class EmployeeList(generics.ListAPIView):
    serializer_class = EmployeeSerializer
    queryset = Employee.objects.all()
