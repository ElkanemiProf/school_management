from django.core.management.base import BaseCommand
from main.models import Student, Subject, SchoolClass, Teacher

class Command(BaseCommand):
    help = 'Assign subjects to classes based on their level'

    def handle(self, *args, **kwargs):
        # Fetch students by their class level and assign subjects accordingly
        junior_classes = SchoolClass.objects.filter(level__startswith='JS')
        senior_classes = SchoolClass.objects.filter(level__startswith='SS')

        # Assign Junior subjects to Junior classes
        junior_subjects = Subject.objects.filter(level='Junior')
        for school_class in junior_classes:
            for subject in junior_subjects:
                # Logic to assign subjects to students or teachers in Junior classes
                # e.g., assigning a teacher or marking subjects for students
                # Example: Assign a subject to a teacher for this class
                teacher = Teacher.objects.filter(subject_taught=subject).first()
                if teacher:
                    school_class.subjects.add(subject)

        # Assign Senior subjects to Senior classes
        senior_subjects = Subject.objects.filter(level='Senior')
        for school_class in senior_classes:
            for subject in senior_subjects:
                # Logic to assign subjects to students or teachers in Senior classes
                teacher = Teacher.objects.filter(subject_taught=subject).first()
                if teacher:
                    school_class.subjects.add(subject)

        self.stdout.write(self.style.SUCCESS('Successfully assigned subjects to classes'))
