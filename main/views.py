from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Avg, Count, Q
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic.edit import CreateView
from django.utils import timezone
from datetime import datetime, timedelta
import json
import csv
import pandas as pd
import logging
from django.db.models.functions import ExtractYear
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.contrib.auth import authenticate, login

# Models
from main.models import (
    Student, Grade, SchoolClass, MaintenanceRequest, Budget, IncidentReport,
    UserProfile, Teacher, Subject, Club, TimeSlot, Timetable, Event, Note,
    AttendanceImage, Notification, Admissions
)

# Forms
from main.forms import (
    MaintenanceRequestForm, StudentForm, UploadClassListForm, IncidentReportForm,
    BudgetForm, RegistrationForm, SubjectForm, EventForm, AttendanceImageForm,
    NoteFormSet, SimpleClubForm
)

# Logger
logger = logging.getLogger(__name__)

# ======================== Helper Functions ========================

def permission_denied_view(request, exception=None):
    """
    Custom 403 Forbidden view.
    """
    return render(request, 'main/pages/samples/error-403.html', status=403)

def get_greeting():
    """Returns a greeting based on the time of day."""
    current_time = timezone.now()
    if current_time.hour < 12:
        return "Good Morning"
    elif 12 <= current_time.hour < 18:
        return "Good Afternoon"
    return "Good Evening"

def save_timetable(timetable, school_class):
    """Saves or updates the timetable in the database."""
    for day, schedule in timetable.items():
        try:
            Timetable.objects.update_or_create(
                school_class=school_class,
                day=day,
                defaults={
                    'period_1': schedule[0],
                    'period_2': schedule[1],
                    'period_3': schedule[2],
                    'period_4': schedule[3],
                    'period_5': schedule[4],
                    'period_6': schedule[5],
                    'period_7': schedule[6],
                    'period_8': schedule[7],
                    'period_9': schedule[8]
                }
            )
        except Exception as e:
            logger.error(f"Error saving timetable for {day}: {e}")

def load_existing_timetable(existing_timetable):
    """Loads a saved timetable from the database, sorted by the day of the week."""
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    timetable = {}
    for entry in existing_timetable.order_by('day'):
        day_schedule = [
            entry.period_1, entry.period_2, entry.period_3, entry.period_4,
            entry.period_5, entry.period_6, entry.period_7, entry.period_8, entry.period_9
        ]
        timetable[entry.day] = day_schedule
    return {day: timetable[day] for day in days_order if day in timetable}

# ======================== Views ========================

# ------------------------ Dashboard ------------------------
from datetime import datetime
from django.utils import timezone

@login_required
@user_passes_test(lambda u: u.userprofile.role in ['teacher', 'principal'])
def dashboard_view(request):
    user = request.user
    try:
        user_profile = user.userprofile
        user_role = user_profile.role
    except AttributeError:
        return redirect('login')

    greeting = f"{get_greeting()}, {user.first_name} {user.last_name} ({user_role})"

    # Counts
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    day_students_count = Student.objects.filter(residency_status='day_student').count()
    boarders_count = Student.objects.filter(residency_status='boarder').count()
    male_students_count = Student.objects.filter(gender='male').count()
    female_students_count = Student.objects.filter(gender='female').count()

    # Budget data
    budgets = Budget.objects.all()
    categories = [budget.category for budget in budgets]
    allocated_amounts = [float(budget.allocated_amount) for budget in budgets]
    spent_amounts = [float(budget.spent_amount) for budget in budgets]

    # Admissions data
    current_year = datetime.now().year

    # Fetch current year admissions for JS1 students
    js1_classes = SchoolClass.objects.filter(level='JS1')  # Get all JS1 classes
    current_year_admissions = 0

    for js1_class in js1_classes:
        # Count students admitted in the current year for each JS1 class
        current_year_admissions += js1_class.students.filter(admission_date__year=current_year).count()

    # Fetch admissions data for all years
    admissions_per_year = Admissions.objects.filter(admission_date__isnull=False) \
        .annotate(admission_year=ExtractYear('admission_date')) \
        .values('admission_year') \
        .annotate(count=Count('id')) \
        .order_by('admission_year')

    # Pair admission_years and admission_counts into a list of dictionaries
    admissions_data = [
        {'year': entry['admission_year'], 'count': entry['count']}
        for entry in admissions_per_year
    ]

    # Debug: Print the query results
    print("Admissions Data:", admissions_data)
    print("Current Year Admissions (JS1):", current_year_admissions)

    # Pending incidents
    pending_incidents = IncidentReport.objects.filter(resolved=False)
    pending_incidents_count = pending_incidents.count()

    # New entries (last 30 days)
    new_budgets = Budget.objects.filter(created_at__gte=timezone.now() - timedelta(days=30))
    new_events = Event.objects.filter(created_at__gte=timezone.now() - timedelta(days=30))
    new_maintenance_requests = MaintenanceRequest.objects.filter(date_requested__gte=timezone.now() - timedelta(days=30))

    context = {
        'greeting': greeting,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'day_students_count': day_students_count,
        'boarders_count': boarders_count,
        'male_students_count': male_students_count,
        'female_students_count': female_students_count,
        'current_year_admissions': current_year_admissions,  # Add this to the context
        'admissions_data': admissions_data,  # Add this to the context
        'admission_years': [entry['year'] for entry in admissions_data],  # For the chart
        'admission_counts': [entry['count'] for entry in admissions_data],  # For the chart
        'categories': categories,
        'allocated_amounts': allocated_amounts,
        'spent_amounts': spent_amounts,
        'pending_incidents_count': pending_incidents_count,
        'new_budgets_count': new_budgets.count(),
        'new_events_count': new_events.count(),
        'new_maintenance_requests_count': new_maintenance_requests.count(),
        'new_pending_incidents': pending_incidents,
        'new_budgets': new_budgets,
        'new_events': new_events,
        'new_maintenance_requests': new_maintenance_requests,
    }
    return render(request, 'main/index.html', context)
# ------------------------ Student Management ------------------------

@login_required
def view_students(request, class_id):
    school_class = get_object_or_404(SchoolClass, id=class_id)
    students = Student.objects.filter(school_class=school_class)
    context = {
        'school_class': school_class,
        'students': students,
        'add_student_url': reverse('add_student', kwargs={'level': school_class.level, 'section': school_class.section}),
        'export_excel_url': reverse('export_class_list', args=[class_id]),
    }
    return render(request, 'main/pages/tables/students_in_class.html', context)

@login_required
def add_student(request, level, section):
    school_class = get_object_or_404(SchoolClass, level=level, section=section)
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            student.school_class = school_class
            student.save()
            messages.success(request, f'{student.first_name} {student.last_name} has been added successfully.')
            return redirect('view_students', class_id=school_class.id)
    else:
        form = StudentForm()
    context = {
        'form': form,
        'class_name': f"{level} {section}",
        'school_class': school_class,
    }
    return render(request, 'main/pages/forms/add_new_student.html', context)

@login_required
def update_student(request, class_id, pk):
    student = get_object_or_404(Student, pk=pk)
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student {student.first_name} {student.last_name}'s details were updated successfully!")
            return redirect('view_students', class_id=school_class.id)
    else:
        form = StudentForm(instance=student)
    return render(request, 'main/pages/forms/update_student.html', {'form': form, 'student': student})

@login_required
def delete_student(request, class_id, student_id):
    student = get_object_or_404(Student, id=student_id, school_class_id=class_id)
    student.delete()
    messages.success(request, 'Student deleted successfully.')
    return redirect('view_students', class_id=class_id)

# ------------------------ Subject Management ------------------------

@login_required
def add_subject_view(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm()
    return render(request, 'main/pages/forms/add_subject.html', {'form': form})

@login_required
def subject_list_view(request):
    level = request.GET.get('level')
    subjects = Subject.objects.filter(level=level) if level else Subject.objects.all()
    return render(request, 'main/pages/tables/subject_list.html', {'subjects': subjects, 'level': level})

@login_required
def modify_subject_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)
    context = {
        'form': form,
        'subject': subject,
        'subject_id': subject_id,
    }
    return render(request, 'main/pages/forms/modify_subject.html', context)

@login_required
def delete_subject_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        subject.delete()
        return redirect('subject_list')
    return render(request, 'main/pages/forms/delete_subject_confirm.html', {'subject': subject})

# ------------------------ Timetable Management ------------------------

@login_required
def generate_timetable_view(request, class_id):
    school_class = get_object_or_404(SchoolClass, id=class_id)
    existing_timetable = Timetable.objects.filter(school_class=school_class).order_by('day')
    if existing_timetable.exists():
        timetable = load_existing_timetable(existing_timetable)
        is_saved = True
    else:
        timetable = generate_new_timetable(school_class)
        is_saved = False

    if request.method == 'POST':
        save_timetable(timetable, school_class)
        return redirect('generate_timetable', class_id=class_id)

    context = {
        'school_class': school_class,
        'timetable': timetable,
        'is_saved': is_saved,
    }
    return render(request, 'main/pages/tables/timetable.html', context)

# ------------------------ Other Views ------------------------

@login_required
def approve_users(request):
    if request.user.userprofile.role != 'principal':
        return render(request, 'main/pages/samples/error-404.html')

    unapproved_users = UserProfile.objects.filter(approved=False)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_profile = get_object_or_404(UserProfile, id=user_id)
        user_profile.approved = True
        user_profile.user.is_active = True
        user_profile.save()
        messages.success(request, f'User {user_profile.user.username} approved successfully.')
        return redirect('approve_users')
    return render(request, 'main/pages/samples/approve_users.html', {'unapproved_users': unapproved_users})

# ======================== AJAX Views ========================

@csrf_exempt
def update_teachers_ajax(request, subject_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        subject = Subject.objects.get(id=subject_id)
        teacher_ids = data.get("teacher_ids", [])
        if not teacher_ids:
            return JsonResponse({"error": "No teachers selected"}, status=400)

        teachers = Teacher.objects.filter(id__in=teacher_ids)
        subject.teacher.set(teachers)
        return JsonResponse({"message": "Teachers updated successfully!"})
   
    except Subject.DoesNotExist:
        return JsonResponse({"error": "Subject not found"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    

@login_required
@user_passes_test(lambda u: u.userprofile.role in ['teacher', 'principal'])

def student_report(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    grades = Grade.objects.filter(student=student)
    
    average_score = grades.aggregate(Avg('score'))['score__avg']
    class_students = Student.objects.filter(school_class=student.school_class)
    class_averages = {s.id: Grade.objects.filter(student=s).aggregate(Avg('score'))['score__avg'] for s in class_students}
    sorted_averages = sorted(class_averages.items(), key=lambda x: x[1], reverse=True)
    class_position = sorted_averages.index((student.id, average_score)) + 1

    context = {
        'student': student,
        'grades': grades,
        'average_score': average_score,
        'class_position': class_position,
    }
    return render(request, 'main/student_report.html', context)


def student_report_excel(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    grades = Grade.objects.filter(student=student)
    
    average_score = grades.aggregate(Avg('score'))['score__avg']
    class_students = Student.objects.filter(school_class=student.school_class)
    class_averages = {s.id: Grade.objects.filter(student=s).aggregate(Avg('score'))['score__avg'] for s in class_students}
    sorted_averages = sorted(class_averages.items(), key=lambda x: x[1], reverse=True)
    class_position = sorted_averages.index((student.id, average_score)) + 1

    grades_data = [[g.subject.name, g.term, g.score, g.grade] for g in grades]
    df = pd.DataFrame(grades_data, columns=['Subject', 'Term', 'Score', 'Grade'])

    summary = pd.DataFrame([['Average Score', average_score], ['Class Position', class_position]], columns=['Description', 'Value'])
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{student.first_name}_report.xlsx"'
    
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Grades')
        summary.to_excel(writer, index=False, sheet_name='Summary')

    return response

# View for listing all maintenance requests
@login_required
@user_passes_test(lambda u: u.userprofile.role in ['teacher', 'principal'])

def maintenance_request_list(request):
    
    requests = MaintenanceRequest.objects.all()
    return render(request, 'main/pages/tables/maintenance_request_list.html', {'requests': requests})

@login_required
def maintenance_request_create(request):
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Maintenance request submitted successfully.')
            return redirect('maintenance_request_list')
    else:
        form = MaintenanceRequestForm()
    return render(request, 'main/pages/forms/maintenance_request_form.html', {'form': form})

def maintenance_request_update(request, pk):
    # Check if the user is not a principal
    
    if request.method == 'POST':
        # Check if the user is not a principal
        if request.user.userprofile.role != 'principal':
            # Redirect to your custom 404 page
            return render(request, 'main/pages/samples/error-404.html')

        form = MaintenanceRequestForm(request.POST, instance=maintenance_request)
        if form.is_valid():
            form.save()
            messages.success(request, 'Maintenance request updated successfully.')
            return redirect('maintenance_request_list')
    else:
        form = MaintenanceRequestForm(instance=maintenance_request)
    return render(request, 'main/pages/forms/maintenance_request_form.html', {'form': form})

def hoverable_school_classes_view(request):
    # Fetch all the school classes
    school_classes = SchoolClass.objects.all()

    # Prepare context data
    class_data = []
    max_students = 35  # Maximum capacity of students per class
    
    for school_class in school_classes:
        student_count = school_class.students.count()  # Assuming you have a reverse relation `students`
        vacant_spaces = max_students - student_count  # Calculate vacant spaces

        class_data.append({
            'id': school_class.id,  # Ensure ID is passed
            'level': school_class.level,
            'section': school_class.section,
            'student_count': student_count,
            'vacant_spaces': vacant_spaces,
            'view_students_url': reverse('view_students', args=[school_class.id]),
            'view_timetable_url': reverse('view_timetable', args=[school_class.id])  # URL for viewing the timetable
        })

    context = {
        'class_data': class_data,
        'total_students': Student.objects.count(),
        'total_male_students': Student.objects.filter(gender='male').count(),
        'total_female_students': Student.objects.filter(gender='female').count(),
        'total_boarders': Student.objects.filter(residency_status='boarder').count(),
        'total_day_students': Student.objects.filter(residency_status='day_student').count(),
    }

    return render(request, 'main/pages/tables/basic-table.html', context)

@login_required
def export_class_list(request, class_id):
    # Fetch the school class and its students
    school_class = get_object_or_404(SchoolClass, id=class_id)
    students = Student.objects.filter(school_class=school_class)

    # Convert the students queryset to a pandas DataFrame
    data = []
    for student in students:
        data.append([student.first_name, student.last_name])

    df = pd.DataFrame(data, columns=['First Name', 'Last Name'])

    # Create a HTTP response with Excel content
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=class_{school_class.level}_{school_class.section}_students.xlsx'

    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Students')
    return response

@login_required
def teacher_list_view(request):
    teachers = Teacher.objects.all().prefetch_related('subject_taught', 'classes_taught')

    # Count total number of teachers
    total_teachers = teachers.count()

    # Corrected Query for Teachers Per Subject
    subjects_with_teachers = {}
    for subject in Subject.objects.all():
        subject_teacher_count = teachers.filter(subject_taught=subject).count()
        subjects_with_teachers[subject.name] = {
            'count': subject_teacher_count,
            'level': subject.level
        }

    # Count teachers per level (Junior & Senior)
    junior_teachers = teachers.filter(subject_taught__level='Junior').distinct().count()
    senior_teachers = teachers.filter(subject_taught__level='Senior').distinct().count()

    context = {
        'teachers': teachers,
        'total_teachers': total_teachers,
        'subjects_with_teachers': subjects_with_teachers,
        'junior_teachers': junior_teachers,
        'senior_teachers': senior_teachers,
    }

    return render(request, 'main/pages/tables/teacher_list.html', context)

@login_required
def student_distribution_view(request):
    # Fetch all class names
    class_names = list(SchoolClass.objects.values_list('level', 'section'))
    class_names = [f"{name[0]} {name[1]}" for name in class_names]

    # Initialize lists to store class-specific data
    male_student_counts = []
    female_student_counts = []
    gender_counts = []
    residency_counts = []
    male_day_students = []
    male_boarders = []
    female_day_students = []
    female_boarders = []

    for level, section in SchoolClass.objects.values_list('level', 'section'):
        # Filter students by class
        male_students = Student.objects.filter(school_class__level=level, school_class__section=section, gender='male').count()
        female_students = Student.objects.filter(school_class__level=level, school_class__section=section, gender='female').count()
        
        day_students = Student.objects.filter(school_class__level=level, school_class__section=section, residency_status='day_student').count()
        boarders = Student.objects.filter(school_class__level=level, school_class__section=section, residency_status='boarder').count()

        # Filter male and female students by residency status
        male_day = Student.objects.filter(school_class__level=level, school_class__section=section, gender='male', residency_status='day_student').count()
        male_boarder = Student.objects.filter(school_class__level=level, school_class__section=section, gender='male', residency_status='boarder').count()
        female_day = Student.objects.filter(school_class__level=level, school_class__section=section, gender='female', residency_status='day_student').count()
        female_boarder = Student.objects.filter(school_class__level=level, school_class__section=section, gender='female', residency_status='boarder').count()

        # Append values to lists
        male_student_counts.append(male_students)
        female_student_counts.append(female_students)
        gender_counts.append([male_students, female_students])  # Store for the gender pie chart
        residency_counts.append([day_students, boarders])  # Store for the residency doughnut chart
        male_day_students.append(male_day)
        male_boarders.append(male_boarder)
        female_day_students.append(female_day)
        female_boarders.append(female_boarder)

    context = {
        'class_names': class_names,
        'male_student_counts': male_student_counts,
        'female_student_counts': female_student_counts,
        'gender_counts': gender_counts,  # Now class-specific
        'residency_counts': residency_counts,  # Now class-specific
        'male_day_students': male_day_students,  # Male day students
        'male_boarders': male_boarders,  # Male boarders
        'female_day_students': female_day_students,  # Female day students
        'female_boarders': female_boarders,  # Female boarders
    }

    return render(request, 'main/pages/charts/student_distribution.html', context)
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import IncidentReportForm
from .models import IncidentReport

def report_incident(request):
    if request.method == 'POST':
        form = IncidentReportForm(request.POST)
        if form.is_valid():
            # Save the form without committing to the database
            incident = form.save(commit=False)
            
            # Set the reported_by_name field (if needed)
            # Since reported_by_name is already in the form, it will be saved automatically
            # No additional handling is required unless you want to process the name further
            
            # Save the incident to the database
            incident.save()
            
            # Add a success message
            messages.success(request, 'Incident reported successfully.')
            
            # Redirect to the incident list or another page
            return redirect('incident_list')
    else:
        form = IncidentReportForm()
    
    return render(request, 'main/pages/forms/report_incident.html', {'form': form})
    
@login_required
@user_passes_test(lambda u: u.userprofile.role in ['teacher', 'principal'])

def incident_list(request):
    incidents = IncidentReport.objects.all().order_by('-date_reported')
    return render(request, 'main/pages/tables/incident_list.html', {'incidents': incidents})

@login_required
def resolve_incident(request, incident_id):
    incident = get_object_or_404(IncidentReport, id=incident_id)
    incident.resolved = True
    incident.save()
    messages.success(request, 'Incident marked as resolved.')
    return redirect('incident_list')

def submit_maintenance_request(request):
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST)
        if form.is_valid():
            maintenance_request = form.save(commit=False)
            # Optionally set the user who submitted the request
            # maintenance_request.request_by = request.user
            maintenance_request.save()
            messages.success(request, 'Maintenance request submitted successfully.')
            return redirect('maintenance_request_list')  # Redirect to the list of maintenance requests
    else:
        form = MaintenanceRequestForm()

    return render(request, 'main/pages/forms/submit_maintenance_request.html', {'form': form})

@login_required
def resolve_maintenance_request(request, request_id):
    maintenance_request = get_object_or_404(MaintenanceRequest, id=request_id)
    maintenance_request.status = 'resolved'
    maintenance_request.save()
    messages.success(request, 'Maintenance request marked as resolved.')
    return redirect('maintenance_request_list')

@login_required
def change_maintenance_status(request, pk):
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    maintenance_request.status = 'resolved'
    maintenance_request.save()
    messages.success(request, 'Maintenance request marked as resolved.')
    return redirect('maintenance_request_list')

@login_required
def edit_maintenance_request(request, pk):
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    
    if request.method == 'POST':
        form = MaintenanceRequestForm(request.POST, instance=maintenance_request)
        if form.is_valid():
            form.save()
            return redirect('maintenance_request_list')  # Redirect to the list of maintenance requests after saving
    else:
        form = MaintenanceRequestForm(instance=maintenance_request)
    
    return render(request, 'main/pages/forms/edit_maintenance_request.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User is not active until approved by Principal
            user.save()

            # Notify the principal for approval
            principal = UserProfile.objects.filter(role='principal').first()
            if principal:
                send_mail(
                    'New User Registration for Approval',
                    f'A new user has registered with the role of {form.cleaned_data["role"]}. Please review and approve the registration.',
                    'admin@example.com',
                    [principal.user.email],
                    fail_silently=False,
                )
            return redirect('registration_success')
    else:
        form = RegistrationForm()
    return render(request, 'main/pages/samples/register.html', {'form': form})

def registration_success(request):
    return render(request, 'main/pages/samples/registration_success.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to the dashboard after login
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'main/pages/samples/login.html')


class EventCreateView(CreateView):
    model = Event
    form_class = EventForm
    template_name = 'main/pages/forms/add_event.html'
    success_url = reverse_lazy('event_list')  # Redirect to the event list after successful submission

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = NoteFormSet(self.request.POST)
        else:
            context['formset'] = NoteFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if form.is_valid() and formset.is_valid():
            event = form.save()  # Save the event
            notes = formset.save(commit=False)  # Save formset without committing to the database

            for note in notes:
                note.event = event  # Associate the note with the event
                note.save()

            messages.success(self.request, "Event and notes created successfully!")  # Success message
            return redirect(self.success_url)
        else:
            messages.error(self.request, "There was an error saving the event.")  # Error message
            return self.render_to_response(context)

    def form_invalid(self, form):
        messages.error(self.request, "Form is invalid. Please correct the errors and try again.")
        return super().form_invalid(form)

def upload_attendance_image(request):
    if request.method == 'POST':
        # Get form data
        teacher_id = request.POST.get('teacher')
        class_name = request.POST.get('class_name')
        attendance_date = request.POST.get('attendance_date')
        uploaded_by = request.POST.get('uploaded_by')
        subject = request.POST.get('subject', '')  # Default to empty string if subject is not provided
        remarks = request.POST.get('remarks')

        try:
            # Find the teacher by ID
            teacher = Teacher.objects.get(id=teacher_id)

            # Create and save the attendance record, allowing subject to be empty
            new_attendance = AttendanceImage.objects.create(
                teacher=teacher,
                class_name=class_name,
                attendance_date=attendance_date,
                uploaded_by=uploaded_by,
                subject=subject if subject else None,  # If subject is empty, save it as None
                remarks=remarks
            )

            # Add success message
            messages.success(request, 'Attendance uploaded successfully!')

            # Redirect to the attendance detail view using the new attendance's ID (pk)
            return redirect('attendance_image_detail', pk=new_attendance.id)

        except Teacher.DoesNotExist:
            # Add error message if the teacher is not found
            messages.error(request, 'The selected teacher does not exist.')
            logger.error(f'Teacher with ID {teacher_id} does not exist.')
        
        except Exception as e:
            # Log the full error for debugging purposes
            logger.error(f"Error occurred while uploading attendance: {str(e)}")
            # Add general error message if something goes wrong
            messages.error(request, 'An error occurred while uploading the attendance. Please try again.')

    # Fetch all teachers from the database
    teachers = Teacher.objects.all()

    # Pass teachers to the template
    return render(request, 'main/pages/attendance/upload_attendance_image.html', {'teachers': teachers})

@require_GET
def get_teacher_details(request):
    teacher_id = request.GET.get('teacher_id')
    try:
        teacher = Teacher.objects.prefetch_related('subject_taught', 'classes_taught').get(id=teacher_id)
        
        # Get subjects and classes
        subjects = [{'name': subject.name, 'level': subject.level} for subject in teacher.subject_taught.all()]
        classes = [{'level': school_class.level, 'section': school_class.section} for school_class in teacher.classes_taught.all()]
        
        return JsonResponse({'subjects': subjects, 'classes': classes})
    except Teacher.DoesNotExist:
        return JsonResponse({'error': 'Teacher not found'}, status=404)


def view_timetable(request, class_id):
    school_class = get_object_or_404(SchoolClass, id=class_id)
    
    # Get all the time slots ordered by start time
    time_slots = TimeSlot.objects.all().order_by('start_time')

    # Filter the timetable entries for this class
    timetable_entries = Timetable.objects.filter(school_class=school_class)

    # Days of the week for the timetable
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Create a dictionary to store the timetable with days of the week and times
    timetable = {}

    for time_slot in time_slots:
        # Create a row for each time slot
        timetable[time_slot] = {}

        for day in days_of_week:
            # Find the timetable entry for the specific day and time slot
            entry = timetable_entries.filter(time_slot=time_slot, time_slot__day_of_week=day).first()
            
            # Add assembly or break information, or the subject/teacher
            if time_slot.is_assembly and day in ['Monday', 'Wednesday', 'Friday']:
                timetable[time_slot][day] = 'Assembly'
            elif time_slot.is_break:
                timetable[time_slot][day] = 'Break'
            elif entry:
                timetable[time_slot][day] = f"{entry.subject.name} ({entry.teacher.user.first_name} {entry.teacher.user.last_name})"
            else:
                timetable[time_slot][day] = ''  # Empty if no subject

    context = {
        'school_class': school_class,
        'timetable': timetable,
        'days_of_week': days_of_week,
    }

    
    return render(request, 'main/pages/timetables/view_timetable.html', context)

@login_required
def generate_timetable_for_class(request, class_id):
    school_class = get_object_or_404(SchoolClass, id=class_id)
    generate_class_timetable(school_class)
    return redirect('view_timetable', class_id=class_id)


def generate_timetable_view(request, class_id):
    """
    View to generate or load a timetable for a specific class.
    """
    school_class = get_object_or_404(SchoolClass, id=class_id)
    
    # Check if a saved timetable already exists for this class
    existing_timetable = Timetable.objects.filter(school_class=school_class).order_by('day')

    if existing_timetable.exists():
        timetable = load_existing_timetable(existing_timetable)
        is_saved = True
    else:
        timetable = generate_new_timetable(school_class)
        is_saved = False

    # Handle saving the timetable
    if request.method == 'POST':
        save_timetable(timetable, school_class)
        return redirect('generate_timetable', class_id=class_id)

    context = {
        'school_class': school_class,
        'timetable': timetable,
        'is_saved': is_saved,
    }
    return render(request, 'main/pages/tables/timetable.html', context)


def timetable_view(request, class_id):
    school_class = get_object_or_404(SchoolClass, id=class_id)
    timetable = Timetable.objects.get(school_class=school_class).schedule

    context = {
        'school_class': school_class,
        'timetable': json.loads(timetable),  # Convert JSON to Python dict
    }
    return render(request, 'main/pages/timetable.html', context)

def edit_timetable_view(request, class_id):
    school_class = SchoolClass.objects.get(id=class_id)
    timetable_entries = Timetable.objects.filter(school_class=school_class)

    if request.method == "POST":
        timetable_data = json.loads(request.POST.get("timetable_data"))

        for day, subjects in timetable_data.items():
            timetable_entry = timetable_entries.filter(day=day).first()
            if timetable_entry:
                timetable_entry.period_1 = subjects[0] if len(subjects) > 0 else ""
                timetable_entry.period_2 = subjects[1] if len(subjects) > 1 else ""
                timetable_entry.period_3 = subjects[2] if len(subjects) > 2 else ""
                timetable_entry.period_4 = subjects[3] if len(subjects) > 3 else ""
                timetable_entry.period_5 = subjects[4] if len(subjects) > 4 else ""
                timetable_entry.period_6 = subjects[5] if len(subjects) > 5 else ""
                timetable_entry.period_7 = subjects[6] if len(subjects) > 6 else ""
                timetable_entry.period_8 = subjects[7] if len(subjects) > 7 else ""
                timetable_entry.period_9 = subjects[8] if len(subjects) > 8 else ""
                timetable_entry.save()

        return redirect("timetable_view", class_id=class_id)

    # Organizing timetable for display
    timetable = {}
    for entry in timetable_entries:
        timetable[entry.day] = [
            entry.period_1 or "",
            entry.period_2 or "",
            entry.period_3 or "",
            entry.period_4 or "",
            entry.period_5 or "",
            entry.period_6 or "",
            entry.period_7 or "",
            entry.period_8 or "",
            entry.period_9 or ""
        ]

    context = {
        "school_class": school_class,
        "timetable": timetable,
    }

    return render(request, "main/pages/timetables/edit_timetable.html", context)


@login_required
def upload_class_list(request, class_id):
    if request.method == 'POST':
        if 'file' in request.FILES:
            csv_file = request.FILES['file']
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)

            fieldnames = {name.lower(): name for name in reader.fieldnames}
            
            for row in reader:
                first_name = row.get(fieldnames.get('first name')) or row.get(fieldnames.get('first_name'))
                last_name = row.get(fieldnames.get('last name')) or row.get(fieldnames.get('last_name'))
                
                if first_name and last_name:
                    Student.objects.create(
                        school_class_id=class_id,
                        first_name=first_name,
                        last_name=last_name,
                    )
            messages.success(request, 'Class list uploaded successfully!')
            return redirect('view_students', class_id=class_id)
        else:
            messages.error(request, 'Please upload a CSV file.')
    return render(request, 'main/pages/forms/upload_class_list.html')



@login_required
def student_payment_status_view(request):
    # Get the search queries for name, classroom, and payment status
    query = request.GET.get('q', '').strip()
    classroom_query = request.GET.get('classroom', '')
    payment_status = request.GET.get('payment_status', '')

    # Base querysets for paid and unpaid students
    paid_students = Student.objects.filter(school_fees_status='paid')
    unpaid_students = Student.objects.filter(school_fees_status='unpaid')

    # Apply name filter
    if query:
        query_parts = query.split()
        if len(query_parts) == 2:
            first_name_query, last_name_query = query_parts
        else:
            first_name_query = last_name_query = query

        paid_students = paid_students.filter(
            Q(first_name__icontains=first_name_query) & Q(last_name__icontains=last_name_query))
        unpaid_students = unpaid_students.filter(
            Q(first_name__icontains=first_name_query) & Q(last_name__icontains=last_name_query)
        )

    # Apply classroom filter
    if classroom_query:
        paid_students = paid_students.filter(school_class_id=classroom_query)
        unpaid_students = unpaid_students.filter(school_class_id=classroom_query)

    # Apply payment status filter
    if payment_status == 'paid':
        unpaid_students = Student.objects.none()  # Exclude unpaid students
    elif payment_status == 'unpaid':
        paid_students = Student.objects.none()  # Exclude paid students

    # Get the counts of paid and unpaid students for the selected classroom
    count_paid = paid_students.count()
    count_unpaid = unpaid_students.count()

    # Fetch all school classes for the dropdown
    school_classes = SchoolClass.objects.all()

    context = {
        'paid_students': paid_students,
        'unpaid_students': unpaid_students,
        'count_paid': count_paid,  # Count of paid students
        'count_unpaid': count_unpaid,  # Count of unpaid students
        'query': query,
        'classroom_query': classroom_query,
        'payment_status': payment_status,  # Pass the selected payment status
        'school_classes': school_classes,
    }

    return render(request, 'main/pages/tables/student_payment_status.html', context)

def select_level_view(request):
    return render(request, 'main/pages/tables/filter_subjects.html')


from functools import wraps



def budget_list(request):
    budgets = Budget.objects.all()
    budget_logs = BudgetLog.objects.all().order_by('-timestamp')  # Fetch all logs
    categories = [budget.category for budget in budgets]
    allocated_amounts = [float(budget.allocated_amount) for budget in budgets]
    spent_amounts = [float(budget.spent_amount) for budget in budgets]

    context = {
        'budgets': budgets,
        'categories': categories,
        'allocated_amounts': allocated_amounts,
        'spent_amounts': spent_amounts,
        'budget_logs': budget_logs,  # Pass logs to the template
    }
    return render(request, 'main/pages/tables/budget_list.html', context)

def login_required_with_budget_id(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        return login_required(view_func)(request, *args, **kwargs)
    return _wrapped_view

@login_required_with_budget_id
def view_budget_logs(request, budget_id):  # Accept budget_id as a positional argument
    # Fetch logs for the specific budget, ordered by timestamp (newest first)
    budget_logs = BudgetLog.objects.filter(budget_id=budget_id).order_by('-timestamp')
    return render(request, 'main/pages/tables/budget_logs.html', {'budget_logs': budget_logs})

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Budget, BudgetLog
from .forms import BudgetForm

@login_required
def create_budget(request):
    # Check if the user is not a principal
    if request.user.userprofile.role != 'principal':
        return render(request, 'main/pages/samples/error-404.html')

    # Continue with the logic for creating a budget if the user is a principal
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save()  # Save the budget first
            messages.success(request, 'Budget created successfully.')

            # Log the creation action
            BudgetLog.objects.create(
                budget=budget,
                user=budget.updated_by,  # Use the updated_by field
                action="Created",
                details=f"Budget for {budget.category} created. Allocated: {budget.allocated_amount}, Spent: {budget.spent_amount}, Remaining: {budget.remaining_amount}"
            )

            return redirect('budget_list')
    else:
        form = BudgetForm()

    return render(request, 'main/pages/forms/create_budget.html', {'form': form})

@login_required
def update_budget(request, pk):
    # Check if the user is not a principal
    if request.user.userprofile.role != 'principal':
        return render(request, 'main/pages/samples/error-404.html')

    # Get the budget object to be updated
    budget = get_object_or_404(Budget, pk=pk)

    # Handle form submission and update the budget if the user is a principal
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            budget = form.save()  # Save the budget
            messages.success(request, 'Budget updated successfully.')

            # Log the update action
            BudgetLog.objects.create(
                budget=budget,
                user=budget.updated_by,  # Use the updated_by field
                action="Updated",
                details=f"Budget for {budget.category} updated. Allocated: {budget.allocated_amount}, Spent: {budget.spent_amount}, Remaining: {budget.remaining_amount}"
            )

            return redirect('budget_list')
    else:
        form = BudgetForm(instance=budget)

    return render(request, 'main/pages/forms/update_budget.html', {'form': form})
from .models import BudgetLog

@login_required
def view_budget_logs(request):
    # Fetch all budget logs, ordered by timestamp (newest first)
    budget_logs = BudgetLog.objects.all().order_by('-timestamp')
    return render(request, 'main/pages/tables/budget_logs.html', {'budget_logs': budget_logs})



@login_required
def delete_budget(request, pk):
    # Check if the user is not a principal
    if request.user.userprofile.role != 'principal':
        # Redirect to your custom 404 page
        return render(request, 'main/pages/samples/error-404.html')

    # Get the budget object to be deleted
    budget = get_object_or_404(Budget, pk=pk)

    # Handle the deletion of the budget if the user is a principal
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted successfully.')
        return redirect('budget_list')

    return render(request, 'main/pages/forms/delete_budget.html', {'budget': budget})

def event_list(request):
    events = Event.objects.prefetch_related('notes').all()  # Fetch events, ordered by date
    context = {
        'events': events
    }
    return render(request, 'main/pages/tables/event_list.html', context)

def add_event(request):
    print("View has been called")  # Check if the view is called

    if request.method == 'POST':
        print("POST request received")  # Check if the form is submitted

        form = EventForm(request.POST)

        if form.is_valid():
            print("Form is valid")  # Check if form validation passes
            event = form.save()

            # Handle notes
            note_contents = request.POST.getlist('note_content')
            print("Notes received:", note_contents)  # Print notes to ensure they're captured

            for content in note_contents:
                if content.strip():
                    Note.objects.create(event=event, content=content)

            messages.success(request, 'Event and notes created successfully!')
            return redirect('event_list')
        else:
            print("Form is invalid:", form.errors)  # Print form errors to console
            messages.error(request, "There was an error saving the event.")
    else:
        form = EventForm()

    return render(request, 'main/pages/forms/add_event.html', {
        'form': form,
    })

def student_search(request):
    # Check if it's an AJAX request by looking at the `HTTP_X_REQUESTED_WITH` header
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        query = request.GET.get('term', '')
        students = Student.objects.filter(first_name__icontains=query)[:10]  # Adjust query as necessary
        results = []
        for student in students:
            student_json = {
                'id': student.id,
                'label': f"{student.first_name} {student.last_name}",
                'value': f"{student.first_name} {student.last_name}"
            }
            results.append(student_json)
        return JsonResponse(results, safe=False)
    return JsonResponse({'error': 'Not an ajax request'}, status=400)

def edit_event(request, id):
    print("View has been called")  # Debugging log

    # Retrieve the event to be edited
    event = get_object_or_404(Event, id=id)
    existing_notes = event.notes.all()  # Get all existing notes linked to the event

    if request.method == 'POST':
        print("POST request received")  # Debugging log

        form = EventForm(request.POST, instance=event)  # Bind the form to the existing event

        if form.is_valid():
            print("Form is valid")  # Debugging log
            event = form.save()  # Save the updated event

            # Handle notes
            note_contents = request.POST.getlist('note_content')
            print("Notes received:", note_contents)  # Debugging log

            # Clear existing notes before saving updated ones
            event.notes.all().delete()

            # Create new notes or update the existing ones
            for content in note_contents:
                if content.strip():  # Avoid saving empty notes
                    Note.objects.create(event=event, content=content)

            messages.success(request, 'Event and notes updated successfully!')
            return redirect('event_list')  # Redirect to event list after successful update
        else:
            print("Form is invalid:", form.errors)  # Debugging log
            messages.error(request, "There was an error updating the event.")
    else:
        form = EventForm(instance=event)

    # Prepare the existing notes to pre-fill the form fields
    note_contents = [note.content for note in existing_notes]

    return render(request, 'main/pages/forms/edit_event.html', {
        'form': form,
        'note_contents': note_contents,  # Pass existing notes to the template
        'event': event
    })

def delete_event(request, id):
    event = get_object_or_404(Event, id=id)
    if request.method == 'POST':
        event.delete()  # Delete the event
        return redirect('event_list')  # Redirect back to the event list after deletion


def search_attendance_records(request):
    # Fetch class names by combining level and section
    class_names = list(SchoolClass.objects.values_list('level', 'section'))
    class_names = [f"{name[0]} {name[1]}" for name in class_names]

    # Initialize records as None to not display anything by default
    records = None
    no_results_message = None  # This will hold the 'no records found' message if needed

    # Get search parameters from the request
    class_name = request.GET.get('class_name')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Remove any extra spaces in the class_name
    if class_name:
        class_name = class_name.replace(" ", "").strip()  # Remove all spaces and trim

    # If search parameters are provided, filter the attendance records
    if class_name or (start_date and end_date):
        records = AttendanceImage.objects.all()

        if class_name:
            records = records.filter(class_name__icontains=class_name)  # Case-insensitive filtering

        # Apply date range filtering only if both start and end dates are provided
        if start_date and end_date:
            try:
                records = records.filter(attendance_date__range=[start_date, end_date])
            except ValueError:
                # Handle the case where date format is invalid
                no_results_message = "Invalid date range provided."
                records = None  # Clear the records in case of error

        # If no records are found, set a message to display in the template
        if not records or not records.exists():
            no_results_message = f"No attendance records found for class {class_name} in the selected date range."

    elif request.GET:  # This handles the case where a search was submitted but without enough parameters
        no_results_message = "Please select a class or a valid date range."

    # Pass the class names, filtered records, and no_results_message to the template
    return render(request, 'main/pages/attendance/attendance_image_list.html', {
        'records': records,
        'class_names': class_names,  # Pass the list of class names to the template
        'no_results_message': no_results_message  # Pass the message to the template
    })

def attendance_image_detail(request, pk):
    # Retrieve the attendance image by its primary key (pk)
    attendance_image = get_object_or_404(AttendanceImage, pk=pk)
    
    return render(request, 'main/pages/attendance/attendance_image_detail.html', {'attendance_image': attendance_image})

def edit_attendance_image(request, pk):
    # Fetch the attendance record
    attendance = get_object_or_404(AttendanceImage, pk=pk)
    
    if request.method == 'POST':
        form = AttendanceImageForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Attendance record updated successfully!')
            return redirect('attendance_image_detail', pk=attendance.pk)
    else:
        form = AttendanceImageForm(instance=attendance)
    
    # Fetch all teachers from the database
    teachers = Teacher.objects.all()
    
    # Pass the form and teachers to the template
    return render(request, 'main/pages/attendance/edit_attendance_image.html', {'form': form, 'attendance': attendance, 'teachers': teachers})


def student_details(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'main/pages/tables/student_details.html', {'student': student})


def list_clubs(request):
    clubs = Club.objects.all()
    return render(request, 'main/pages/clubs/list_clubs.html', {'clubs': clubs})

def create_club(request):
    if request.method == 'POST':
        form = SimpleClubForm(request.POST)
        if form.is_valid():
            club = form.save(commit=False)

            student_names = form.cleaned_data['student_names']
            teacher_names = form.cleaned_data['teacher_names']

            # Handle students
            student_objects = []
            for full_name in student_names:
                try:
                    first_name, last_name = full_name.split(' ', 1)
                    # Use filter to get all students matching the name
                    students = Student.objects.filter(first_name=first_name, last_name=last_name)
                    if students.exists():
                        student_objects.extend(students)  # Add all matching students
                    else:
                        messages.error(request, f"Student '{full_name}' does not exist.")
                        return render(request, 'main/pages/clubs/club_form.html', {'form': form})
                except ValueError:
                    messages.error(request, f"Student name '{full_name}' must include both first and last name.")
                    return render(request, 'main/pages/clubs/club_form.html', {'form': form})

            # Handle teachers
            teacher_objects = []
            for full_name in teacher_names:
                try:
                    first_name, last_name = full_name.split(' ', 1)
                    # Use filter to get all teachers matching the name
                    teachers = Teacher.objects.filter(user__first_name=first_name, user__last_name=last_name)
                    if teachers.exists():
                        teacher_objects.extend(teachers)  # Add all matching teachers
                    else:
                        messages.error(request, f"Teacher '{full_name}' does not exist.")
                        return render(request, 'main/pages/clubs/club_form.html', {'form': form})
                except ValueError:
                    messages.error(request, f"Teacher name '{full_name}' must include both first and last name.")
                    return render(request, 'main/pages/clubs/club_form.html', {'form': form})

            # Save the club
            club.save()

            # Assign students and teachers
            club.students.set(student_objects)
            club.teachers.set(teacher_objects)
            
            messages.success(request, "Club created successfully!")
            return redirect('list_clubs')  # Redirect to club list view
    else:
        form = SimpleClubForm()

    return render(request, 'main/pages/clubs/club_form.html', {'form': form})
    
def view_club(request, pk):
    club = get_object_or_404(Club, pk=pk)  # Use pk here
    
    # Get the students and teachers
    students = club.students.all()
    teachers = club.teachers.all()
    
    return render(request, 'main/pages/clubs/view_club.html', {
        'club': club,
        'students': students,
        'teachers': teachers
    })

def edit_club(request, pk):
    club = get_object_or_404(Club, pk=pk)

    if request.method == 'POST':
        form = SimpleClubForm(request.POST, instance=club)
        if form.is_valid():
            form.save()
            messages.success(request, "Club updated successfully!")
            return redirect('list_clubs')
    else:
        form = SimpleClubForm(instance=club)

    return render(request, 'main/pages/clubs/club_form.html', {'form': form, 'club': club})

# Delete a club
def delete_club(request, pk):
    club = get_object_or_404(Club, pk=pk)
    if request.method == 'POST':
        club.delete()
        return redirect('list_clubs')
    return render(request, 'main/pages/clubs/delete_club.html', {'club': club})



from django.db.models import Count, Q
from django.db.models.functions import ExtractYear
from main.models import Admissions

def admissions_list(request):
    # Fetch the admission years, total admissions, and admitted counts per year
    admissions_years = Admissions.objects.annotate(year=ExtractYear('admission_date')) \
                                         .values('year') \
                                         .annotate(
                                             count=Count('id'),  # Total admissions
                                             admitted_count=Count('id', filter=Q(admission_status='accepted'))  # Admitted count
                                         ) \
                                         .order_by('-year')
    
    # Debug: Print the admissions_years queryset to the console
    for year_data in admissions_years:
        print(year_data)
    
    context = {
        'admissions_years': admissions_years
    }
    return render(request, 'main/pages/admissions/admissions_list.html', context)


def admissions_by_year(request, year):
    # Fetch admissions for the given year
    admissions = Admissions.objects.filter(admission_date__year=year)

    context = {
        'year': year,
        'admissions': admissions,
    }
    return render(request, 'main/pages/admissions/admissions_by_year.html', context)

def mark_notifications_as_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('dashboard')  # Redirect to the dashboard after marking as read


def update_teachers_ajax(request, subject_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        # Load JSON data from request body
        data = json.loads(request.body)

        # Get the subject
        subject = Subject.objects.get(id=subject_id)

        # Ensure teacher_ids exist
        teacher_ids = data.get("teacher_ids", [])
        if not teacher_ids:
            return JsonResponse({"error": "No teachers selected"}, status=400)

        # Update teachers
        teachers = Teacher.objects.filter(id__in=teacher_ids)
        subject.teacher.set(teachers)  # Ensure this is ManyToManyField

        return JsonResponse({"message": "Teachers updated successfully!"})
   
    except Subject.DoesNotExist:
        return JsonResponse({"error": "Subject not found"}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    

@login_required
def delete_incident(request, incident_id):
    # Fetch the incident or return a 404 error if it doesn't exist
    incident = get_object_or_404(IncidentReport, id=incident_id)
    
    # Delete the incident
    incident.delete()
    
    # Add a success message
    messages.success(request, 'Incident deleted successfully.')
    
    # Redirect to the incident list
    return redirect('incident_list')



@login_required
def resolve_incident(request, incident_id):
    # Fetch the incident or return a 404 error if it doesn't exist
    incident = get_object_or_404(IncidentReport, id=incident_id)
    
    # Mark the incident as resolved
    incident.resolved = True
    incident.status = 'resolved'  # Update the status if you have a status field
    incident.save()
    
    # Add a success message
    messages.success(request, f'Incident "{incident.incident_type}" has been marked as resolved.')
    
    # Redirect to the incident list
    return redirect('incident_list')


from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .models import IncidentReport
from django.utils import timezone

def update_incident(request, id):
    # Fetch the incident or return a 404 error if it doesn't exist
    incident_report = get_object_or_404(IncidentReport, id=id)
    
    if request.method == 'POST':
        # Get the new comments from the form
        new_comments = request.POST.get('comments')
        
        # Append the new comments to the existing comments with a timestamp
        if new_comments.strip():  # Ensure new_comments is not empty
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            updated_comments = f"{incident_report.comments}\n\n[{timestamp}] {new_comments}" if incident_report.comments else f"[{timestamp}] {new_comments}"
            incident_report.comments = updated_comments
        
        # Update other fields if needed
        incident_report.incident_type = request.POST.get('incident_type')
        incident_report.description = request.POST.get('description')
        incident_report.location = request.POST.get('location')
        
        # Save the updated incident
        incident_report.save()
        
        # Add a success message
        messages.success(request, 'Incident updated successfully.')
        
        # Redirect to the incident list or another page
        return redirect('incident_list')
    
    # Pass the incident_report variable to the template
    return render(request, 'main/pages/forms/update_incident.html', {'incident': incident_report})

def student_autocomplete(request):
    term = request.GET.get('term', '')
    students = Student.objects.filter(
        Q(first_name__icontains=term) | Q(last_name__icontains=term)
    ).values_list('first_name', 'last_name')

    # Format the results as a list of strings (e.g., "John Doe")
    results = [f"{first_name} {last_name}" for first_name, last_name in students]
    return JsonResponse(results, safe=False)
