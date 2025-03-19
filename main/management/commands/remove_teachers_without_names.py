from django.core.management.base import BaseCommand
from main.models import Teacher
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Removes all Teacher instances where the associated User has no first name or last name.'

    def handle(self, *args, **kwargs):
        # Find teachers without a first name or last name
        teachers_to_delete = Teacher.objects.filter(
            user__first_name__isnull=True,  # No first name
            user__last_name__isnull=True    # No last name
        )

        # Count the number of teachers to be deleted
        count = teachers_to_delete.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No teachers without first or last names found.'))
            return

        # Delete the teachers
        teachers_to_delete.delete()

        # Output the result
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} teachers without first or last names.'))