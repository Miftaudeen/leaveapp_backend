from datetime import datetime, date
from django.template.defaultfilters import date as format_date
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction


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

    employee = models.ForeignKey(User, related_name='employee_leaves', on_delete=models.CASCADE)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    leave_policy = models.ForeignKey(LeavePolicy, on_delete=models.PROTECT)
    submission_date = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField()
    end_date = models.DateField()
    days_taken = models.IntegerField(default=0)
    leave_balance = models.FloatField(editable=False)
    relief = models.ForeignKey(User, related_name='relief_leaves', null=True, blank=True,
                               help_text="Notice will be sent to your relief", on_delete=models.PROTECT)
    status = models.PositiveIntegerField(choices=STATUS, default=PENDING, editable=False)
    remarks = models.TextField(null=True, blank=True)
    handover_note = models.FileField(upload_to=get_employee_hon_upload_path, null=True, blank=True,
                                     help_text="Upload a document containing handover instructions")

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

    def save(self):
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
