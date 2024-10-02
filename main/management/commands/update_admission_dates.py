from django.core.management.base import BaseCommand
from main.models import Student
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Update admission dates based on the class level of the student'

    def handle(self, *args, **kwargs):
        # Define the class levels and the years to subtract
        class_levels = {
            'SS3': 6,
            'SS2': 5,
            'SS1': 4,
            'JS3': 3,
            'JS2': 2,
            'JS1': 1,
        }

        # Get the current date
        current_year = timezone.now().year

        # Iterate through each student and adjust the admission date
        for student in Student.objects.all():
            level = student.school_class.level
            if level in class_levels:
                years_to_subtract = class_levels[level]
                adjusted_admission_date = timezone.now().replace(year=current_year - years_to_subtract)
                student.admission_date = adjusted_admission_date
                student.save()

                self.stdout.write(self.style.SUCCESS(f"Updated {student.first_name} {student.last_name}'s admission date to {student.admission_date}"))
