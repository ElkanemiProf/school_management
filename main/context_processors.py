from django.urls import resolve
from django.shortcuts import render
from .models import FeePayment, IncidentReport, MaintenanceRequest, Budget, UserProfile

def fee_totals(request):
    # Check if the current view is FeePaymentAdmin
    if resolve(request.path_info).url_name == 'main_feepayment_changelist':
        total_paid = FeePayment.objects.filter(status='Paid').count()
        total_unpaid = FeePayment.objects.filter(status='Unpaid').count()
        return {
            'total_paid': total_paid,
            'total_unpaid': total_unpaid,
        }
    return {}

def navbar_context(request):
    # Fetch unread notifications
    new_incidents = IncidentReport.objects.filter(resolved=False)
    new_requests = MaintenanceRequest.objects.filter(status='pending')
    new_budgets = Budget.objects.filter(remaining_amount__lt=0)  # Example: Notify if budget overspent
    unapproved_users = UserProfile.objects.filter(approved=False)  # Notify for unapproved users

    notifications = []

    # Incident notifications
    for incident in new_incidents:
        notifications.append({
            'message': f"New incident report: {incident.description[:30]}...",
            'url': 'incident_list',  # Adjust URL as needed
            'timestamp': incident.date_reported,
        })

    # Maintenance request notifications
    for request in new_requests:
        notifications.append({
            'message': f"New maintenance request: {request.description[:30]}...",
            'url': 'maintenance_request_list',  # Adjust URL as needed
            'timestamp': request.date_requested,
        })

    # Budget notifications (Example: Alert on overspending)
    for budget in new_budgets:
        notifications.append({
            'message': f"Overspent budget: {budget.category}...",
            'url': 'budget_list',  # Adjust URL as needed
            'timestamp': budget.updated_at,  # Assuming there's an updated_at field in your Budget model
        })

    # New user registration notifications
    for user in unapproved_users:
        notifications.append({
            'message': f"New user registration: {user.user.username}",
            'url': 'approve_users',  # Adjust URL as needed
            'timestamp': user.user.date_joined,
        })

    # Sort notifications by timestamp, newest first
    notifications.sort(key=lambda x: x['timestamp'], reverse=True)

    context = {
        'notifications': notifications,
        'new_notifications_count': len(notifications),
    }

    return context
