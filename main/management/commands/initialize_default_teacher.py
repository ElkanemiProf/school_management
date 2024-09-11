from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from main.models import Teacher

class Command(BaseCommand):
    help = 'Creates a default teacher user'

    def handle(self, *args, **options):
        # Ensure that the default teacher doesn't already exist
        if not User.objects.filter(username='default_teacher').exists():
            # Create a default user for the teacher
            user = User.objects.create_user(username='default_teacher', password='password123')
            
            # Create a default teacher
            default_teacher = Teacher.objects.create(user=user, phone_number='1234567890', ippis_number='IPPIS123')
            self.stdout.write(self.style.SUCCESS('Successfully created default teacher'))
        else:
            self.stdout.write(self.style.WARNING('Default teacher already exists'))
