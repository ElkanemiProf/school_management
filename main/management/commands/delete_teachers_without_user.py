from django.core.management.base import BaseCommand
from main.models import Teacher

class Command(BaseCommand):
    help = 'Deletes all Teacher instances that do not have an associated User.'

    def handle(self, *args, **kwargs):
        # Find all Teacher instances without a User
        teachers_without_user = Teacher.objects.filter(user__isnull=True)

        # Count the number of teachers to be deleted
        count = teachers_without_user.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No teachers without a User found.'))
            return

        # Delete the teachers
        teachers_without_user.delete()

        # Output the result
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} teachers without a User.'))