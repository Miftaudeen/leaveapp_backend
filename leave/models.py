from datetime import datetime, date, timedelta

from django.contrib.auth.models import Group
from django.template.defaultfilters import date as format_date
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from dateutil import rrule
from dateutil.relativedelta import relativedelta



def get_employee_hon_upload_path(instance, filename):
    dt = datetime.today()
    return 'employees/leave/{0}/{1}/{2}/{3}'.format(dt.year, dt.month, instance.employee.username, filename)


class LeaveType(models.Model):
    """
    Define leave categories e.g. annual leave, sick, maternity etc.
    """
    name = models.CharField(max_length=50, unique=True)
    paid = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class LeavePolicy(models.Model):
    """
    Leave Policies contain definitions of leave types
    """
    leave_type = models.ForeignKey(LeaveType, related_name='policies', on_delete=models.CASCADE)
    num_days = models.PositiveIntegerField(help_text='Number of days employee is entitled to per annum',
                                           validators=[MinValueValidator(1)])
    max_carry_over = models.PositiveIntegerField(default=0,
                                                 help_text='Number of days an employee can carry over from one year to the next.')
    group = models.ForeignKey(Group, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.leave_type)


class Leave(models.Model):
    """
    Manage staff leave history.

    Assumes a five-day work week, where all employees can apply for all leave types.
    Future: System will trigger the start of the leave after it has been approved on leave start date.
    Resumption from leave should be triggered by employee.
    Available leave after this one is taken, counting from the end date, is captured
    by the leave_balance field.

    Leave allowance is implemented here, using the PayrollMixin. A pay variable is provided and used in configuring leave allowances in pay templates.
    """
    PENDING, APPROVED, RUNNING, RETURNED, CANCELLED, REJECTED = range(6)
    STATUS = (
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (RUNNING, 'Running'),
        (RETURNED, 'Returned'),
        (CANCELLED, 'Cancelled'),
        (REJECTED, 'Rejected'),
    )

    employee = models.ForeignKey('employees.Employee', related_name='employee_leaves', on_delete=models.CASCADE)
    changed_by = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, null=True)
    leave_policy = models.ForeignKey(LeavePolicy, on_delete=models.PROTECT)
    submission_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField()
    end_date = models.DateField()
    days_taken = models.IntegerField(default=0)
    leave_balance = models.FloatField(editable=False)
    relief = models.ForeignKey('employees.Employee', related_name='relief_leaves', null=True, blank=True,
                               help_text="Notice will be sent to your relief", on_delete=models.PROTECT)
    status = models.PositiveIntegerField(choices=STATUS, default=PENDING, editable=False)
    remarks = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Leave'
        verbose_name_plural = 'Leave'
        ordering = ('-id',)
        permissions = (
            ('can_approve_leave', 'Can approve leave'),
            ('can_manage_leave', 'Can manage leave'),
        )

    def __str__(self):
        return u'%s: %s (%s - %s)' % (
            self.employee, self.leave_policy,
            format_date(self.start_date, 'jS M'),
            format_date(self.end_date, 'jS M'))

    def save(self, **kwargs):
        if self.leave_balance < 0:
            raise ValidationError('You only have %s days left on %s leave type.' % (
            int(self.days_taken + self.leave_balance), self.leave_policy.leave_type))
        else:
            super(Leave, self).save()

    def is_pending(self):
        return self.status == Leave.PENDING

    @property
    def can_start(self):
        """Returns `True` if this leave can be started."""
        return self.start_date <= date.today() < self.end_date

    @transaction.atomic
    def change_status(self, new_status, changed_by):
        """Change this leave's status."""
        if new_status:
            self.status = new_status
            self.changed_by = changed_by
            self.save()


def get_number_working_days(start_date, end_date):
    """
    Get the number of working days between start_date and end_date

    excluding the end date. and public holidays
    """
    if start_date >= end_date:
        raise ValueError('The end date must come after the start date')
    stop_date = end_date + timedelta(-1)
    dates = list(rrule.rrule(rrule.DAILY, dtstart=start_date, until=stop_date, byweekday=(0, 1, 2, 3, 4)))
    return len(dates)


class LeavePeriod(object):
    """
    Represents a period between the start and end dates for a particular leave year
    """

    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date


VALID_LEAVE = (
    Leave.RUNNING,
    Leave.RETURNED,
    Leave.APPROVED
)


class EmployeeLeaveStructure(object):
    """
    Container for leave periods
    """

    def __init__(self, employee, leave_policy, ref_date=None):
        """
        ref_date is date available leave is being calculated for,
        usually (but not necessarily) today
        """
        self.employee = employee
        if not ref_date:
            self.ref_date = date.today()
        else:
            self.ref_date = ref_date
        self.policy = leave_policy
        try:
            self.last_leave = Leave.objects.filter(
                employee=employee,
                leave_policy=self.policy,
                status__in=VALID_LEAVE).order_by('-start_date')[0]
        except IndexError:
            # no leave taken?
            self.last_leave = None

    def get_leave_period(self, ref_date, leave_start_month):
        # what is leave period for ref_date (usually current)?
        if ref_date.month < leave_start_month:
            # period started last year
            start_date = date(ref_date.year - 1, leave_start_month, 1)
        else:
            # period started this year
            start_date = date(ref_date.year, leave_start_month, 1)
        end_date = start_date + relativedelta(years=1) - relativedelta(days=1)
        return LeavePeriod(start_date, end_date)

    def calculate_leave_days(self, leave_start_month):
        """
        TODO: pro-rating of leave days
        """
        period = self.get_leave_period(self.ref_date, leave_start_month)
        if self.last_leave:
            # did emp take leave within current period?
            if period.start_date <= self.last_leave.start_date <= period.end_date:
                leave_balance = self.last_leave.leave_balance
                # adjust for change in policy if needed
                leave_balance += self.policy.num_days - self.last_leave.leave_policy.num_days
            else:
                # leave not taken in immediate past period
                last_period_start = period.start_date - relativedelta(years=1)
                last_period_end = period.start_date - relativedelta(days=1)
                leave_balance = self.policy.num_days
                if last_period_start <= self.last_leave.start_date <= last_period_end:
                    # leave taken in immediate past period
                    carry_over = min(self.last_leave.leave_policy.max_carry_over,
                                     self.last_leave.leave_balance)
                else:
                    # leave taken at least 2 periods before current period, use last policy
                    carry_over = min(self.last_leave.leave_policy.max_carry_over,
                                     self.last_leave.leave_policy.num_days)
                leave_balance += carry_over
        else:
            # emp has not taken any leave days at all, use current policy
            leave_balance = self.policy.num_days
            if period.start_date > self.employee.hire_date:
                # there may be carry overs
                leave_balance += min(self.policy.max_carry_over, self.policy.num_days)
        return leave_balance

