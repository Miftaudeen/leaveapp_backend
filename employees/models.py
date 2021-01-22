from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

from django.utils.translation import ugettext_lazy as _
# Create your models here.


class EmployeeManager(BaseUserManager):

    def create_user(self, username, hire_date, last_name, first_name, middle_name, email, password=None):
        employee = self.model(
            username=username,
            hire_date=hire_date,
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            email=self.normalize_email(email)
        )

        employee.set_password(password)
        employee.save(using=self._db)
        return employee

    def create_superuser(self, username, hire_date, last_name, first_name, middle_name, email, password):
        employee = self.create_user(
            username, hire_date, last_name, first_name, middle_name, email, password)
        employee.is_superuser = True
        employee.is_staff = True
        employee.save(using=self._db)
        return employee


class Employee(AbstractUser):
    REQUIRED_FIELDS = ['last_name', 'first_name', 'middle_name', 'hire_date', 'email' ]
    last_name = models.CharField(verbose_name=_('Surname'), max_length=50)
    first_name = models.CharField(verbose_name=_('First name'), max_length=50)
    middle_name = models.CharField(verbose_name=_(
        'Middle name'), max_length=50, blank=True, null=True)
    hire_date = models.DateField()
    groups = models.ManyToManyField(Group, related_name='employees')
    user_permissions = models.ManyToManyField(Permission, related_name='employees')

    objects = EmployeeManager()


