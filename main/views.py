from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Avg
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, user_passes_test
from main.models import Student, Grade, SchoolClass, MaintenanceRequest, Budget, IncidentReport, UserProfile,Teacher
from main.forms import MaintenanceRequestForm, StudentForm, UploadClassListForm, IncidentReportForm, BudgetForm, RegistrationForm
import pandas as pd
from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
import csv
# Import the Subject model at the top of the views.py file
from .models import Subject,IncidentReport, Club  
from django.utils import timezone

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from main.models import UserProfile,Notification
import datetime
from datetime import datetime
from django.shortcuts import render, redirect
from .forms import AttendanceImageForm,NoteFormSet
from .models import AttendanceImage
from .models import Event, Note,Admissions
from .forms import EventForm
from django.utils import timezone
from datetime import timedelta
import logging
from django.db.models import Count
from django.db.models.functions import ExtractYear

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


@login_required
def approve_users(request):
    # Check if the user is not a principal
    if request.user.userprofile.role != 'principal':
        # Redirect to your custom 404 page
        return render(request, 'main/pages/samples/error-404.html')

    # Logic for approving users if the user is a principal
    unapproved_users = UserProfile.objects.filter(approved=False)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_profile = get_object_or_404(UserProfile, id=user_id)
        user_profile.approved = True
        user_profile.user.is_active = True  # Activate the user
        user_profile.user.save()
        user_profile.save()
        messages.success(request, f'User {user_profile.user.username} approved successfully.')
        return redirect('approve_users')

    return render(request, 'main/pages/samples/approve_users.html', {'unapproved_users': unapproved_users})

# View for generating student report as HTML
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

# View for generating student report as Excel
@login_required
@user_passes_test(lambda u: u.userprofile.role in ['teacher', 'principal'])

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

# View for creating a new maintenance request
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

# View for updating an existing maintenance request
@login_required


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

# View for changing maintenance request status
@login_required
def change_maintenance_status(request, pk):
    maintenance_request = get_object_or_404(MaintenanceRequest, pk=pk)
    maintenance_request.status = 'resolved'
    maintenance_request.save()
    messages.success(request, 'Maintenance request marked as resolved.')
    return redirect('maintenance_request_list')

# Dashboard view
# Ensure only users with specific roles can access
@user_passes_test(lambda u: u.is_authenticated and hasattr(u, 'userprofile') and u.userprofile.role in ['teacher', 'principal'])
@login_required
 # Ensure the Note model is imported



def dashboard_view(request):
    user = request.user

    # Safely fetch the user's profile and role
    try:
        user_profile = user.userprofile
        user_role = user_profile.role  # Fetch the role from the UserProfile
    except AttributeError:
        return redirect('login')  # Redirect to login or another appropriate page

    # Get the current time
    current_time = timezone.now()

    # Determine the greeting based on the time of day
    if current_time.hour < 12:
        greeting = "Good Morning"
    elif 12 <= current_time.hour < 18:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    full_greeting = f"{greeting}, {request.user.first_name} {request.user.last_name} ({user_role})"

    # Count total students, teachers, and other student categories
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    day_students_count = Student.objects.filter(residency_status='day_student').count()
    boarders_count = Student.objects.filter(residency_status='boarder').count()
    male_students_count = Student.objects.filter(gender='male').count()
    female_students_count = Student.objects.filter(gender='female').count()

    # Budget data for the bar chart
    budgets = Budget.objects.all()
    categories = [budget.category for budget in budgets]
    allocated_amounts = [float(budget.allocated_amount) for budget in budgets]
    spent_amounts = [float(budget.spent_amount) for budget in budgets]

    # Admissions data from the Student model for the current year (2023)
    current_year = datetime.now().year
    current_year_admissions = Student.objects.filter(admission_date__year=2023).count()

    # Admissions per year (last 6 years)
    admissions_per_year = Student.objects.filter(
        admission_date__year__gte=current_year - 6
    ).annotate(
        admission_year=ExtractYear('admission_date')
    ).values('admission_year').annotate(
        count=Count('id')
    ).order_by('admission_year')

    # Extract years and counts into separate lists
    admission_years = [entry['admission_year'] for entry in admissions_per_year]
    admission_counts = [entry['count'] for entry in admissions_per_year]

    # Count pending incidents
    pending_incidents = IncidentReport.objects.filter(resolved=False)
    pending_incidents_count = pending_incidents.count()

    # Track newly created budgets (last 30 days)
    new_budgets = Budget.objects.filter(created_at__gte=timezone.now() - timedelta(days=30))
    new_budgets_count = new_budgets.count()

    # Track newly created events (last 30 days)
    new_events = Event.objects.filter(created_at__gte=timezone.now() - timedelta(days=30))
    new_events_count = new_events.count()

    # Track newly created maintenance requests (last 30 days)
    new_maintenance_requests = MaintenanceRequest.objects.filter(date_requested__gte=timezone.now() - timedelta(days=30))
    new_maintenance_requests_count = new_maintenance_requests.count()

    # Prepare the context to pass to the template
    context = {
        'greeting': full_greeting,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'day_students_count': day_students_count,
        'boarders_count': boarders_count,
        'male_students_count': male_students_count,
        'female_students_count': female_students_count,
        'current_year_admissions': current_year_admissions,
        'admission_years': admission_years,  # Pass the list of years
        'admission_counts': admission_counts,  # Pass the list of counts
        'categories': categories,
        'allocated_amounts': allocated_amounts,
        'spent_amounts': spent_amounts,
        'pending_incidents_count': pending_incidents_count,  # Pass pending incidents count
        'new_budgets_count': new_budgets_count,  # Pass newly created budgets count
        'new_events_count': new_events_count,  # Pass newly created events count
        'new_maintenance_requests_count': new_maintenance_requests_count,  # Pass newly created maintenance requests count
        'new_pending_incidents': pending_incidents,  # Pass pending incidents list
        'new_budgets': new_budgets,  # Pass new budgets list
        'new_events': new_events,  # Pass new events list
        'new_maintenance_requests': new_maintenance_requests,  # Pass new maintenance requests list
    }

    return render(request, 'main/index.html', context)




# View for displaying students in a class
@login_required
@user_passes_test(lambda u: u.userprofile.role in ['teacher', 'principal'])

def view_students(request, class_id):
    school_class = get_object_or_404(SchoolClass, id=class_id)
    students = Student.objects.filter(school_class=school_class)
    
    add_student_url = reverse('add_student', kwargs={'level': school_class.level, 'section': school_class.section})
    export_excel_url = reverse('export_class_list', args=[class_id])
    
    context = {
        'school_class': school_class,
        'students': students,
        'add_student_url': add_student_url,
        'export_excel_url': export_excel_url,
    }
    return render(request, 'main/pages/tables/students_in_class.html', context)

# View for adding a student to a class
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

# View for updating a student's information
@login_required


def update_student(request, class_id, pk):
    student = get_object_or_404(Student, pk=pk)
    
    # Ensure class_id is passed correctly
    school_class = get_object_or_404(SchoolClass, pk=class_id)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student {student.first_name} {student.last_name}'s details were updated successfully!")
            return redirect('view_students', class_id=school_class.id)
        else:
            messages.error(request, "There was an error updating the student details. Please check the form.")
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'main/pages/forms/update_student.html', {'form': form, 'student': student})

# View for deleting a student
@login_required
def delete_student(request, class_id, student_id):
    student = get_object_or_404(Student, id=student_id, school_class_id=class_id)
    student.delete()
    messages.success(request, 'Student deleted successfully.')
    return redirect('view_students', class_id=class_id)

# View for handling file upload for class lists
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

# View for listing all budgets
@login_required
@user_passes_test(lambda u: u.userprofile.role == 'principal')


def budget_list(request):
    # Fetch all budget data
    budgets = Budget.objects.all()

    # Prepare data for Chart.js
    categories = [budget.category for budget in budgets]
    allocated_amounts = [float(budget.allocated_amount) for budget in budgets]
    spent_amounts = [float(budget.spent_amount) for budget in budgets]

    # Pass the data to the template
    context = {
        'budgets': budgets,
        'categories': categories,
        'allocated_amounts': allocated_amounts,
        'spent_amounts': spent_amounts,
    }
    return render(request, 'main/pages/tables/budget_list.html', context)

# View for creating a new budget
@login_required
def create_budget(request):
    # Check if the user is not a principal
    if request.user.userprofile.role != 'principal':
        # Redirect to your custom 404 page
        return render(request, 'main/pages/samples/error-404.html')

    # Continue with the logic for creating a budget if the user is a principal
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget created successfully.')
            return redirect('budget_list')
    else:
        form = BudgetForm()

    return render(request, 'main/pages/forms/create_budget.html', {'form': form})

# View for updating a budget
@login_required
def update_budget(request, pk):
    # Check if the user is not a principal
    if request.user.userprofile.role != 'principal':
        # Redirect to your custom 404 page
        return render(request, 'main/pages/samples/error-404.html')

    # Get the budget object to be updated
    budget = get_object_or_404(Budget, pk=pk)

    # Handle form submission and update the budget if the user is a principal
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, 'Budget updated successfully.')
            return redirect('budget_list')
    else:
        form = BudgetForm(instance=budget)

    return render(request, 'main/pages/forms/update_budget.html', {'form': form})

# View for deleting a budget
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

# View for registering new users
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

# View for displaying registration success
def registration_success(request):
    return render(request, 'main/pages/samples/registration_success.html')

@login_required

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
            'level': school_class.level,
            'section': school_class.section,
            'student_count': student_count,
            'vacant_spaces': vacant_spaces,  # Add vacant spaces to class data
            'view_students_url': reverse('view_students', args=[school_class.id])
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
from .forms import SubjectForm
@login_required
def add_subject_view(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('subject_list')  # Redirect to a list of subjects or another page after saving
    else:
        form = SubjectForm()

    return render(request, 'main/pages/forms/add_subject.html', {'form': form})

@login_required
def subject_list_view(request):
    subjects = Subject.objects.all()
    return render(request, 'main/pages/tables/subject_list.html', {'subjects': subjects})

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

    return render(request, 'main/pages/forms/modify_subject.html', {'form': form})

@login_required
def delete_subject_view(request, subject_id):
    subject = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        subject.delete()
        return redirect('subject_list')
    return render(request, 'main/pages/forms/delete_subject_confirm.html', {'subject': subject})

@login_required
def teacher_list_view(request):
    teachers = Teacher.objects.all().prefetch_related('subject_taught', 'classes_taught')
    return render(request, 'main/pages/tables/teacher_list.html', {'teachers': teachers})

@login_required
def student_distribution_view(request):
    # Data for Stacked Bar Chart - Student Distribution by Gender and Class
    class_names = list(SchoolClass.objects.values_list('level', 'section'))
    class_names = [f"{name[0]} {name[1]}" for name in class_names]
    
    male_student_counts = []
    female_student_counts = []
    
    for level, section in SchoolClass.objects.values_list('level', 'section'):
        male_student_counts.append(Student.objects.filter(school_class__level=level, school_class__section=section, gender='male').count())
        female_student_counts.append(Student.objects.filter(school_class__level=level, school_class__section=section, gender='female').count())

    # Data for Pie Chart - Gender Distribution
    male_students = Student.objects.filter(gender='male').count()
    female_students = Student.objects.filter(gender='female').count()
    gender_counts = [male_students, female_students]

    # Data for Doughnut Chart - Day Students vs Boarders
    day_students = Student.objects.filter(residency_status='day_student').count()
    boarders = Student.objects.filter(residency_status='boarder').count()
    residency_counts = [day_students, boarders]

    context = {
        'class_names': class_names,
        'male_student_counts': male_student_counts,
        'female_student_counts': female_student_counts,
        'gender_counts': gender_counts,
        'residency_counts': residency_counts,
    }

    return render(request, 'main/pages/charts/student_distribution.html', context)

@login_required
@user_passes_test(lambda u: u.userprofile.role in ['teacher', 'principal'])

def report_incident(request):
    if request.method == 'POST':
        form = IncidentReportForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            # You might want to set a default user if `reported_by` is required
            # incident.reported_by = request.user
            incident.save()
            messages.success(request, 'Incident reported successfully.')
            return redirect('incident_list')  # Redirect to the list of incidents or a confirmation page
    else:
        form = IncidentReportForm()

    return render(request, 'main/pages/forms/report_incident.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.userprofile.role in ['teacher', 'principal'])

def incident_list(request):
    incidents = IncidentReport.objects.all()
    return render(request, 'main/pages/tables/incident_list.html', {'incidents': incidents})

@login_required
def resolve_incident(request, incident_id):
    incident = get_object_or_404(IncidentReport, id=incident_id)
    incident.resolved = True
    incident.save()
    messages.success(request, 'Incident marked as resolved.')
    return redirect('incident_list')

@login_required
@user_passes_test(lambda u: u.userprofile.role in ['teacher', 'principal'])

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


from django.db.models import Q


@login_required
def student_payment_status_view(request):
    # Get the search queries for name and classroom
    query = request.GET.get('q', '').strip()
    classroom_query = request.GET.get('classroom', '')

    # Base querysets for paid and unpaid students
    paid_students = Student.objects.filter(school_fees_status='paid')
    unpaid_students = Student.objects.filter(school_fees_status='unpaid')

    if query:
        query_parts = query.split()
        if len(query_parts) == 2:
            first_name_query, last_name_query = query_parts
        else:
            first_name_query = last_name_query = query

        paid_students = paid_students.filter(
            Q(first_name__icontains=first_name_query) & Q(last_name__icontains=last_name_query)
        )
        unpaid_students = unpaid_students.filter(
            Q(first_name__icontains=first_name_query) & Q(last_name__icontains=last_name_query)
        )

    if classroom_query:
        paid_students = paid_students.filter(school_class_id=classroom_query)
        unpaid_students = unpaid_students.filter(school_class_id=classroom_query)

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
        'school_classes': school_classes,
    }

    return render(request, 'main/pages/tables/student_payment_status.html', context)



from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

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


from django.shortcuts import render
from .models import UserProfile

# View to show notifications for pending approvals
def pending_approvals_view(request):
    if request.user.userprofile.role == 'principal':
        unapproved_users = UserProfile.objects.filter(approved=False)
        return {'pending_approvals': unapproved_users.count()}  # Returning count of unapproved users
    return {'pending_approvals': 0}

from django.shortcuts import render

# Custom 403 Forbidden View
def permission_denied_view(request, exception=None):
    return render(request, 'main/pages/samples/error-404.html', status=403)


from django.shortcuts import render


def event_list(request):
    events = Event.objects.prefetch_related('notes').all()  # Fetch events, ordered by date
    context = {
        'events': events
    }
    return render(request, 'main/pages/tables/event_list.html', context)


# Get an instance of a logger
logger = logging.getLogger(__name__)


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


from django.http import JsonResponse


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



from django.shortcuts import get_object_or_404, redirect
from .models import Event

def delete_event(request, id):
    event = get_object_or_404(Event, id=id)
    if request.method == 'POST':
        event.delete()  # Delete the event
        return redirect('event_list')  # Redirect back to the event list after deletion




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


def attendance_image_list(request):
    # Retrieve all attendance images from the database
    images = AttendanceImage.objects.all()
    
    return render(request, 'main/pages/attendance/attendance_image_list.html', {'images': images})


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

import logging

logger = logging.getLogger(__name__)
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


def student_details(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'main/pages/tables/student_details.html', {'student': student})


from django.shortcuts import render, get_object_or_404, redirect
from .models import Club
from .forms import SimpleClubForm

# List all clubs
def list_clubs(request):
    clubs = Club.objects.all()
    return render(request, 'main/pages/clubs/list_clubs.html', {'clubs': clubs})


from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Club, Student, Teacher
from .forms import SimpleClubForm

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



def admissions_list(request):
   # Fetch the admission years and count the number of admissions per year
    admissions_years = Student.objects.annotate(year=ExtractYear('admission_date')) \
                                      .values('year') \
                                      .annotate(count=Count('id')) \
                                      .order_by('-year')
    
    context = {
        'admissions_years': admissions_years
    }
    return render(request, 'main/pages/admissions/admissions_list.html', context)



def admissions_by_year(request, year):
    # Fetch admissions for the given year
    admissions = Student.objects.filter(admission_date__year=year)

    context = {
        'year': year,
        'admissions': admissions,
    }
    return render(request, 'main/pages/admissions/admissions_by_year.html', context)




def mark_notifications_as_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect('dashboard')  # Redirect to the dashboard after marking as read
