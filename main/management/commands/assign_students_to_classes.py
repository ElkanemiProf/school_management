from django.core.management.base import BaseCommand
from main.models import Student, SchoolClass
import random

class Command(BaseCommand):
    help = 'Assigns students to school classes'

    def handle(self, *args, **options):
        # Fetch all classes
        all_classes = list(SchoolClass.objects.all())
        
        # Fetch all students who do not have a class assigned
        students = Student.objects.filter(school_class__isnull=True)

        # Randomly assign students to classes
        for student in students:
            assigned_class = random.choice(all_classes)
            student.school_class = assigned_class
            student.save()
            self.stdout.write(self.style.SUCCESS(f'Assigned {student.first_name} {student.last_name} to {assigned_class.level} {assigned_class.section}'))
