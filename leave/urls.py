
# URLs for the API
from django.urls import path
from django.views.decorators.cache import cache_page

from employees.api import EmployeeList
from leave.api import LeaveList, LeaveTypeList, LeavePolicyList, LeaveCreate

urlpatterns = [
    path('leaves/', LeaveList.as_view()),
    path('leaves/create/', LeaveCreate.as_view()),
    path('leave/types/', LeaveTypeList.as_view()),
    path('leave/policies/', LeavePolicyList.as_view()),
    path('employees/', EmployeeList.as_view())
]
