from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

import json  # Required to store the dictionary properly


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('principal', 'Principal'),  # Add Principal here
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

class SchoolClass(models.Model):
    LEVEL_CHOICES = [
        ('JS1', 'JS1'),
        ('JS2', 'JS2'),
        ('JS3', 'JS3'),
        ('SS1', 'SS1'),
        ('SS2', 'SS2'),
        ('SS3', 'SS3'),
    ]
    
    SECTION_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]

    level = models.CharField(max_length=3, choices=LEVEL_CHOICES)
    section = models.CharField(max_length=1, choices=SECTION_CHOICES)

    class Meta:
        unique_together = ('level', 'section')
        verbose_name = 'School Class'
        verbose_name_plural = 'School Classes'

    def __str__(self):
        return f'{self.level} {self.section}'

class Subject(models.Model):
    LEVEL_CHOICES = [
        ('Junior', 'Junior'),
        ('Senior', 'Senior'),
    ]

    name = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)  # Non-nullable now
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f'{self.name} - {self.level}'

class Student(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]
    RESIDENCY_STATUS_CHOICES = [
        ('boarder', 'Boarder'),
        ('day_student', 'Day Student'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    date_of_birth = models.DateField(default='2000-01-01')  # Default value
    admission_date = models.DateField(default=timezone.now)
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='students')
    school_fees_status = models.CharField(max_length=6, choices=[('paid', 'Paid'), ('unpaid', 'Unpaid')])
    residency_status = models.CharField(max_length=12, choices=RESIDENCY_STATUS_CHOICES)
    guardians_name = models.CharField(max_length=100, blank=True, null=True)
    guardians_phone_number = models.CharField(max_length=15, blank=True, null=True)
    parents_name = models.CharField(max_length=100, blank=True, null=True)
    parents_phone_number = models.CharField(max_length=15, blank=True, null=True)


    def get_fee_status(self):
        last_payment = self.feepayment_set.order_by('-payment_date').first()
        if last_payment:
            return last_payment.status
        return "Unpaid"

    def __str__(self):
        return f'{self.first_name} {self.last_name}'
    
class Admissions(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='admissions')
    admission_date = models.DateField(default=timezone.now)
    admission_status = models.CharField(max_length=50, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')])
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    admission_remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.first_name} {self.student.last_name} - {self.school_class}"


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=[('present', 'Present'), ('absent', 'Absent')])
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f'{self.student} - {self.date} - {self.status}'

class AttendanceImage(models.Model):
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE, null=True, blank=True)
    class_name = models.CharField(max_length=10)
    attendance_date = models.DateField()
    uploaded_by = models.CharField(max_length=255)
    subject = models.CharField(max_length=100, null=True, blank=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Attendance for {self.class_name} on {self.attendance_date}"

class Exam(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f'{self.student} - {self.subject} - {self.score}'

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    children = models.ManyToManyField(Student, related_name='parents')

    def __str__(self):
        return self.user.username

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subject_taught = models.ManyToManyField(Subject, related_name='teachers')
    phone_number = models.CharField(max_length=15)
    ippis_number = models.CharField(max_length=20)
    classes_taught = models.ManyToManyField('SchoolClass', related_name='teachers')

    def __str__(self):
        return self.user.username

from django.db import models

class MaintenanceRequest(models.Model):
    REQUEST_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
    ]

    request_by = models.CharField(max_length=255, null=True, blank=True)  # If you make this a ForeignKey, ensure `null=True`
    description = models.TextField(null=True, blank=True)
    date_requested = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    location = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default='pending', null=True, blank=True)

    def __str__(self):
        return f"{self.description} - {self.status}"


class FeePayment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[('Paid', 'Paid'), ('Unpaid', 'Unpaid')])

    def __str__(self):
        return f"{self.student} - {self.amount_paid} - {self.status}"
from django.db import models
from django.contrib.auth.models import User

class IncidentReport(models.Model):
    INCIDENT_TYPE_CHOICES = [
        ('bullying', 'Bullying'),
        ('harassment', 'Harassment'),
        ('vandalism', 'Vandalism'),
        ('theft', 'Theft'),
        ('other', 'Other'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
    ]

    CATEGORY_CHOICES = [
        ('bullying', 'Bullying'),
        ('vandalism', 'Vandalism'),
        ('theft', 'Theft'),
        ('other', 'Other'),
    ]

    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reported_incidents', default=1)  # Replace '1' with the appropriate default user ID
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPE_CHOICES, null=True, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField()
    location = models.CharField(max_length=255, null=True, blank=True)
    date_reported = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    resolved = models.BooleanField(default=False)
    comments = models.TextField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='reported')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents')
    resolution_details = models.TextField(null=True, blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    reported_by_name = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Incident reported by {self.reported_by.username} on {self.date_reported}"




class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.CharField(max_length=50)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.term} - {self.grade}"

class Event(models.Model):
    name = models.CharField(max_length=100)  # Event name
    date = models.DateField()  # Event date
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.date})"
    
class Note(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="notes")  # Link each note to an event
    content = models.TextField()  # Note content

    def __str__(self):
        return f"Note for {self.event.name}"
class AuditTrail(models.Model):
    ACTION_CHOICES = [
        ('Create', 'Create'),
        ('Update', 'Update'),
        ('Delete', 'Delete'),
        ('Login', 'Login'),
        ('Logout', 'Logout'),
    ]

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey('Staff', on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"{self.action} by {self.performed_by} on {self.date.strftime('%Y-%m-%d %H:%M:%S')}"

from django.db import models

class Budget(models.Model):
    category = models.CharField(max_length=100)
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)  # New field

    def save(self, *args, **kwargs):
        self.remaining_amount = self.allocated_amount - self.spent_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.category} - Allocated: {self.allocated_amount} - Remaining: {self.remaining_amount}"
class BudgetLog(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='logs')
    user = models.CharField(max_length=100, blank=True, null=True)
    action = models.CharField(max_length=100)  # Action performed (e.g., "Created", "Updated", "Deleted")
    details = models.TextField(blank=True)  # Details of the change
    timestamp = models.DateTimeField(auto_now_add=True)  # Time of the change

    def __str__(self):
        return f"{self.budget.category} - {self.action} by {self.user} at {self.timestamp}"

class Staff(models.Model):
    ROLE_CHOICES = [
        ('Teacher', 'Teacher'),
        ('Administrator', 'Administrator'),
        ('Support Staff', 'Support Staff'),
    ]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=15)
    attendance_records = models.ManyToManyField(Attendance, related_name='staff_members')

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.role}"

from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=FeePayment)
def track_fee_payment(sender, instance, created, **kwargs):
    if created:
        action = 'Create'
        details = f"New fee payment of {instance.amount_paid} for student {instance.student}."
    else:
        action = 'Update'
        details = f"Updated fee payment record for student {instance.student}. Amount: {instance.amount_paid}."
    
    AuditTrail.objects.create(
        action=action,
        performed_by=instance.staff,  # Assuming you have a staff field in FeePayment
        details=details
    )



class Club(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    students = models.ManyToManyField(Student)
    teachers = models.ManyToManyField(Teacher)
    def __str__(self):
        return self.name


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:20]}"



class TimeSlot(models.Model):
    day_of_week = models.CharField(max_length=20)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    # Add fields to track assembly and break times
    is_assembly = models.BooleanField(default=False)
    is_break = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.day_of_week}: {self.start_time} - {self.end_time}"



class Timetable(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE)
    day = models.CharField(max_length=10, default='Monday')
    period_1 = models.CharField(max_length=100, null=True, blank=True)
    period_2 = models.CharField(max_length=100, null=True, blank=True)
    period_3 = models.CharField(max_length=100, null=True, blank=True)
    period_4 = models.CharField(max_length=100, null=True, blank=True)
    period_5 = models.CharField(max_length=100, null=True, blank=True)
    period_6 = models.CharField(max_length=100, null=True, blank=True)
    period_7 = models.CharField(max_length=100, null=True, blank=True)
    period_8 = models.CharField(max_length=100, null=True, blank=True)
    period_9 = models.CharField(max_length=100, null=True, blank=True)

    # ✅ Add this new field to store schedule as JSON
    schedule = models.JSONField(default=dict, blank=True, null=True)

    def __str__(self):
        return f"Timetable for {self.school_class.level} {self.school_class.section} on {self.day}"

