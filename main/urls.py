from django.urls import path
from .views import student_report, student_report_excel
from .views import maintenance_request_list, maintenance_request_create, maintenance_request_update
from .views import dashboard_view
from . import views
from .views import hoverable_school_classes_view, view_students, export_class_list,add_subject_view,subject_list_view,modify_subject_view,delete_subject_view,teacher_list_view
from .views import student_distribution_view,report_incident,incident_list,resolve_incident
from .views import submit_maintenance_request, maintenance_request_list, resolve_maintenance_request,change_maintenance_status,edit_maintenance_request,approve_users
from .views import register, registration_success
from .views import login_view,EventCreateView
from django.contrib.auth.views import LogoutView
from django.conf.urls import handler403
from .views import permission_denied_view
from django.conf import settings
from django.conf.urls.static import static


handler403 = permission_denied_view

urlpatterns = [
    path('student_report/<int:student_id>/', student_report, name='student_report'),
    path('student_report_excel/<int:student_id>/', student_report_excel, name='student_report_excel'),
    path('maintenance-requests/', maintenance_request_list, name='maintenance_request_list'),
    path('maintenance-requests/create/', maintenance_request_create, name='maintenance_request_create'),
    path('maintenance-requests/<int:pk>/edit/', maintenance_request_update, name='maintenance_request_update'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('school_classes/', hoverable_school_classes_view, name='hoverable_school_classes'),
    path('school_class/<int:class_id>/students/', view_students, name='view_students'),
    path('school_class/<int:class_id>/students/export/', export_class_list, name='export_class_list'),
    path('school_class/<str:level> <str:section>/add_student/', views.add_student, name='add_student'),
    path('school_class/<int:class_id>/students/update/<int:pk>/', views.update_student, name='update_student'),
    path('school_class/<int:class_id>/students/delete/<int:student_id>/', views.delete_student, name='delete_student'),
    path('school_class/<int:class_id>/upload_class_list/', views.upload_class_list, name='upload_class_list'),


    path('student-payment-status/', views.student_payment_status_view, name='student_payment_status'),
    path('add-subject/', add_subject_view, name='add_subject'),
    path('subjects/', subject_list_view, name='subject_list'),
    path('subjects/modify/<int:subject_id>/', modify_subject_view, name='modify_subject'),
    path('subjects/delete/<int:subject_id>/', delete_subject_view, name='delete_subject'),
    path('teachers/', teacher_list_view, name='teacher_list'),
    path('student-distribution/', student_distribution_view, name='student_distribution'),

    path('report-incident/', report_incident, name='report_incident'),
    path('incidents/', incident_list, name='incident_list'),
    path('resolve-incident/<int:incident_id>/', resolve_incident, name='resolve_incident'),
    path('submit-maintenance-request/', submit_maintenance_request, name='submit_maintenance_request'),
    path('maintenance-request-list/', maintenance_request_list, name='maintenance_request_list'),
    path('resolve-maintenance-request/<int:request_id>/', resolve_maintenance_request, name='resolve_maintenance_request'),
    path('maintenance-request/<int:pk>/change-status/', change_maintenance_status, name='change_maintenance_status'),
    path('maintenance-request/<int:pk>/edit/', edit_maintenance_request, name='edit_maintenance_request'),

    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/create/', views.create_budget, name='create_budget'),
    path('budgets/update/<int:pk>/', views.update_budget, name='update_budget'),
    path('budgets/delete/<int:pk>/', views.delete_budget, name='delete_budget'),  
    path('approve-users/', views.approve_users, name='approve_users'),
    path('register/', register, name='register'),
    path('registration-success/', registration_success, name='registration_success'),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    path('events/', views.event_list, name='event_list'),
    path('events/', views.event_list, name='event_list'),  # For viewing events
    path('events/add/', views.add_event, name='add_event'),

    path('student-search/', views.student_search, name='student_search'),
    path('events/edit/<int:id>/', views.edit_event, name='edit_event'),  # For editing events
    path('events/delete/<int:id>/', views.delete_event, name='delete_event'),  # For deleting events

    # URL for uploading an attendance image
    path('upload/', views.upload_attendance_image, name='upload_attendance_image'),

    # URL for listing all attendance records
    path('attendance/', views.search_attendance_records, name='attendance_image_list'),

    # URL for viewing the details of a specific attendance record
    path('attendance/<int:pk>/', views.attendance_image_detail, name='attendance_image_detail'),
    path('attendance/<int:pk>/edit/', views.edit_attendance_image, name='edit_attendance_image'),
    path('attendance/search/', views.search_attendance_records, name='attendance_search'),  # For the search form

    path('student/<int:pk>/', views.student_details, name='student_details'),

    path('clubs/', views.list_clubs, name='list_clubs'),  # URL for listing all clubs
    path('clubs/new/', views.create_club, name='create_club'),  # URL for creating a new club
    path('clubs/<int:pk>/', views.view_club, name='view_club'),  # URL for viewing a specific club
    path('clubs/<int:pk>/edit/', views.edit_club, name='edit_club'),  # URL for editing a club
    path('clubs/<int:pk>/delete/', views.delete_club, name='delete_club'),  # URL for deleting a club

    path('admissions/', views.admissions_list, name='admissions_list'),  # List of years
    path('admissions/<int:year>/', views.admissions_by_year, name='admissions_by_year'),  # Admissions by year

    path('notifications/mark-as-read/', views.mark_notifications_as_read, name='mark_notifications_as_read'),





    




    












    



]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)