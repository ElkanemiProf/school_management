from django import forms
from django.contrib import admin
from django.urls import path, reverse
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.html import format_html
import pandas as pd
from .models import (
    Student, Attendance, SchoolClass, UserProfile, Parent, Teacher,
    MaintenanceRequest, FeePayment, IncidentReport, Subject, Grade,
    Event, AuditTrail, Budget, Staff
)
from django.contrib.auth.models import User
from django.db.models import Avg, Max, Min

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
    change_list_template = "admin/student_grade_list.html"

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

    def ordinal_suffix(self, n):
        if 11 <= (n % 100) <= 13:
            return f"{n}th"
        else:
            suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
            return f"{n}{suffixes.get(n % 10, 'th')}"

    def subject_performance_view(self, request, subject_id):
        subject = Subject.objects.get(id=subject_id)
        grades = Grade.objects.filter(subject=subject).order_by('-score')
        avg_score = grades.aggregate(Avg('score'))['score__avg']
        max_score = grades.aggregate(Max('score'))['score__max']
        min_score = grades.aggregate(Min('score'))['score__min']
        rankings = []
        for idx, grade in enumerate(grades, start=1):
            rank_with_suffix = self.ordinal_suffix(idx)
            rankings.append({
                'student': grade.student,
                'score': grade.score,
                'rank': rank_with_suffix,
            })
        best_grade = grades.first()
        best_student = best_grade.student if best_grade else None
        recommendations = []
        if best_student:
            student_grades = Grade.objects.filter(student=best_student)
            weakest_subject = student_grades.order_by('score').first()
            class_students = Student.objects.filter(school_class=best_student.school_class)
            overall_grades = Grade.objects.filter(student__in=class_students).values('student').annotate(total_avg=Avg('score')).order_by('-total_avg')
            rank = next((index + 1 for index, g in enumerate(overall_grades) if g['student'] == best_student.id), None)
            if rank:
                rank_with_suffix = self.ordinal_suffix(rank)
                recommendations.append(f"{best_student.first_name} is currently the {rank_with_suffix} best overall student in {best_student.school_class} and can become the best student if they improve in {weakest_subject.subject.name}.")
            if avg_score and avg_score < 50:
                recommendations.append("The average score is below 50. Consider revising teaching methods or offering additional support to students.")
            if max_score and max_score > 95:
                recommendations.append(f"Great job! {best_student.first_name} scored {max_score}. Keep encouraging high achievers.")
            if min_score and min_score < 40:
                recommendations.append("Some students are struggling significantly. Provide extra help to those scoring below 40.")
            if weakest_subject and weakest_subject.score < 60:
                recommendations.append(f"Encourage {best_student.first_name} to focus more on {weakest_subject.subject.name}, where they scored {weakest_subject.score}.")
            if avg_score and 60 <= avg_score < 70:
                recommendations.append("The average performance is decent, but there is room for improvement. Motivate students to aim higher.")
        context = {
            'subject': subject,
            'avg_score': avg_score,
            'max_score': max_score,
            'min_score': min_score,
            'best_student': best_student,
            'rankings': rankings,
            'recommendations': recommendations if recommendations else ["No recommendations at this time."],
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

    def changelist_view(self, request, extra_context=None):
        # Retrieve all school classes
        school_classes = SchoolClass.objects.all()

        # Count the total number of students
        total_students = Student.objects.count()
        total_male_students = Student.objects.filter(gender='male').count()
        total_female_students = Student.objects.filter(gender='female').count()

        total_boarders = Student.objects.filter(residency_status='boarder').count() or 0
        total_day_students = Student.objects.filter(residency_status='day_student').count() or 0

        # Prepare context data
        extra_context = extra_context or {}
        extra_context['total_students'] = total_students
        extra_context['total_male_students'] = total_male_students
        extra_context['total_female_students'] = total_female_students
        extra_context['total_boarders'] = total_boarders
        extra_context['total_day_students'] = total_day_students
        extra_context['school_classes'] = school_classes  # Pass the list of school classes to the template

        # Render the hoverable table template with the school class data
        return render(request, 'main/pages/hoverable_school_classes.html', extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:class_id>/students/', self.admin_site.admin_view(self.students_list), name='schoolclass_students_list'),
            path('<int:class_id>/students/export/', self.admin_site.admin_view(self.export_class_to_excel), name='schoolclass_students_export'),
        ]
        return custom_urls + urls

    def students_list(self, request, class_id):
        school_class = SchoolClass.objects.get(id=class_id)
        students = Student.objects.filter(school_class=school_class)

        male_students = students.filter(gender='male').count()
        female_students = students.filter(gender='female').count()

        add_student_url = reverse('admin:main_student_add') + f"?school_class={class_id}"
        export_excel_url = reverse('admin:schoolclass_students_export', args=[class_id])

        context = {
            'school_class': school_class,
            'students': students,
            'add_student_url': add_student_url,
            'export_excel_url': export_excel_url,
            'male_students': male_students,
            'female_students': female_students,
        }

        return render(request, 'main/pages/hoverable_school_classes.html', context)

    def export_class_to_excel(self, request, class_id):
        school_class = SchoolClass.objects.get(id=class_id)
        students = Student.objects.filter(school_class=school_class)

        data = []
        for student in students:
            data.append([student.first_name, student.last_name, student.date_of_birth])

        df = pd.DataFrame(data, columns=['First Name', 'Last Name', 'Date of Birth'])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=class_{school_class.level}_{school_class.section}_students.xlsx'

        with pd.ExcelWriter(response, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Students')

        return response


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


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
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


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('category', 'allocated_amount', 'spent_amount', 'remaining_amount')
    readonly_fields = ('remaining_amount',)  # Make remaining_amount readonly as it's calculated

from django.contrib import admin
from .models import UserProfile

# Register UserProfile model in admin
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

admin.site.register(Parent)
admin.site.register(Event)
admin.site.register(AuditTrail)
admin.site.register(Grade)
