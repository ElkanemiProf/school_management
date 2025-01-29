from django import forms
from django.contrib import admin
from django.urls import path, reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import format_html
import pandas as pd
from django.contrib.auth.models import User
from django.db.models import Avg, Max, Min

from .models import (
    Student, Attendance, SchoolClass, UserProfile, Parent, Teacher,
    MaintenanceRequest, FeePayment, IncidentReport, Subject, Grade,
    Event, AuditTrail, Budget, Staff, Club
)

class TeacherAdminForm(forms.ModelForm):
    first_name = forms.CharField(label='First Name')
    last_name = forms.CharField(label='Last Name')
    username = forms.CharField(label='Username')

    class Meta:
        model = Teacher
        fields = '__all__'
        exclude = ['user']  # Exclude the user field from the form

    def save(self, commit=True):
        # Create the new User
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
        )
        # Link the newly created user to the teacher
        self.instance.user = user
        return super().save(commit=commit)

# Custom Admin for Teacher model
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    form = TeacherAdminForm
    list_display = ['get_username', 'get_subjects_taught', 'get_classes_taught', 'phone_number', 'ippis_number']
    search_fields = ['user__username', 'phone_number', 'ippis_number']
    filter_horizontal = ['subject_taught', 'classes_taught']

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_subjects_taught(self, obj):
        return ", ".join([subject.name for subject in obj.subject_taught.all()])
    get_subjects_taught.short_description = 'Subjects Taught'

    def get_classes_taught(self, obj):
        return ", ".join([str(school_class) for school_class in obj.classes_taught.all()])
    get_classes_taught.short_description = 'Classes Taught'


# Custom Form for Staff Admin
class StaffForm(forms.ModelForm):
    first_name = forms.CharField()
    last_name = forms.CharField()
    username = forms.CharField()
    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=[
        ('teacher', 'Teacher'),
        ('administrator', 'Administrator'),
        ('non_teaching_staff', 'Non-Teaching Staff'),
        ('principal', 'Principal'),
    ])

    class Meta:
        model = Staff
        fields = ['phone_number', 'role']

    def save(self, commit=True):
        user = User.objects.create(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data.get('email', '')
        )
        self.instance.user = user
        self.instance.role = self.cleaned_data['role']
        return super().save(commit=commit)


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    form = StaffForm
    list_display = ['get_username', 'first_name', 'last_name', 'role']
    search_fields = ['user__first_name', 'user__last_name', 'phone_number']

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.exclude(role__iexact='principal')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'school_class', 'date_of_birth', 'admission_date', 'get_fee_status')
    search_fields = ('first_name', 'last_name', 'date_of_birth', 'admission_date')
    list_filter = ('school_class', 'date_of_birth', 'admission_date', 'gender', 'school_fees_status')

    def get_fee_status(self, obj):
        return obj.get_fee_status()

    def changelist_view(self, request, extra_context=None):
        search_query = request.GET.get('q', '')
        students = Student.objects.filter(first_name__icontains=search_query) | Student.objects.filter(last_name__icontains=search_query) if search_query else Student.objects.all()

        extra_context = extra_context or {}
        student_grades = {student: Grade.objects.filter(student=student) for student in students}
        extra_context.update({
            'student_grades': student_grades,
            'search_query': search_query
        })

        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:student_id>/export/', self.admin_site.admin_view(self.export_student_excel), name='export_student_excel'),
        ]
        return custom_urls + urls

    def export_student_excel(self, request, student_id):
        student = Student.objects.get(id=student_id)
        grades = Grade.objects.filter(student=student)
        grades_data = [[grade.subject.name, grade.term, grade.score, grade.grade] for grade in grades]
        df = pd.DataFrame(grades_data, columns=['Subject', 'Term', 'Score', 'Grade'])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename={student.first_name}_grades.xlsx'
        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Grades')

        return response


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'description', 'view_performance']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('subject-performance/<int:subject_id>/', self.admin_site.admin_view(self.subject_performance_view), name='subject_performance'),
        ]
        return custom_urls + urls

    def view_performance(self, obj):
        url = reverse('admin:subject_performance', args=[obj.id])
        return format_html('<a href="{}">View Performance</a>', url)
    view_performance.short_description = 'Performance'

    def subject_performance_view(self, request, subject_id):
        subject = Subject.objects.get(id=subject_id)
        grades = Grade.objects.filter(subject=subject).order_by('-score')
        avg_score = grades.aggregate(Avg('score'))['score__avg']
        max_score = grades.aggregate(Max('score'))['score__max']
        min_score = grades.aggregate(Min('score'))['score__min']

        context = {
            'subject': subject,
            'avg_score': avg_score,
            'max_score': max_score,
            'min_score': min_score,
            'rankings': grades,
        }
        return render(request, 'admin/subject_performance.html', context)


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('level', 'section', 'student_count', 'view_students')

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = 'Number of Students'

    def view_students(self, obj):
        return format_html('<a href="{}">View Students</a>', f'{obj.id}/students/')
    view_students.short_description = 'Students'


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('request_by', 'date_requested', 'status', 'location')
    readonly_fields = ('date_requested',)
    list_filter = ('status', 'location')


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ['incident_type', 'reported_by', 'date_reported', 'resolved']
    list_filter = ['incident_type', 'resolved']
    search_fields = ['description', 'location']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'allocated_amount', 'spent_amount', 'remaining_amount')
    readonly_fields = ('remaining_amount',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'approved')  # Show the user, role, and approval status
    list_filter = ('role', 'approved')           # Enable filtering by role and approval status
    search_fields = ('user__username',)          # Allow searching by username
    actions = ['approve_selected_users']         # Add a custom action to approve users

    def approve_selected_users(self, request, queryset):
        queryset.update(approved=True)
    approve_selected_users.short_description = "Approve selected users"


# Register remaining models
admin.site.register(Attendance)
admin.site.register(Club)
admin.site.register(Parent)
admin.site.register(Event)
admin.site.register(AuditTrail)
admin.site.register(Grade)
