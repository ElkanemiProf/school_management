from django.core.management.base import BaseCommand
from faker import Faker
import random
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from main.models import Teacher, Subject, SchoolClass, AttendanceImage  # Update import to use 'main'

fake = Faker()

class Command(BaseCommand):
    help = 'Generates fake attendance data for all classes, each teacher, and each subject.'

    def handle(self, *args, **kwargs):
        # Delete existing fake attendance data
        self.delete_existing_attendance()

        # Generate new data
        teachers = self.generate_teachers()
        school_classes = self.generate_school_classes()
        subjects = self.generate_subjects()

        # Generate attendance data for all combinations
        for teacher in teachers:
            for school_class in school_classes:
                for subject in subjects:
                    self.generate_attendance(teacher, school_class, subject)

        self.stdout.write(self.style.SUCCESS('Successfully generated attendance data for all classes, teachers, and subjects.'))

    def delete_existing_attendance(self):
        # Delete all existing attendance records
        deleted_count, _ = AttendanceImage.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing attendance records.'))

    def generate_teachers(self):
        # Fetch real teachers from the database
        teachers = Teacher.objects.all()
        if not teachers.exists():
            self.stdout.write(self.style.WARNING('No real teachers found in the database.'))
        return teachers

    def generate_school_classes(self):
        levels = ['JS1', 'JS2', 'JS3', 'SS1', 'SS2', 'SS3']
        sections = ['A', 'B', 'C', 'D']
        school_classes = []
        for level in levels:
            for section in sections:
                school_class, created = SchoolClass.objects.get_or_create(
                    level=level,  # Use the `level` field
                    section=section  # Use the `section` field
                )
                school_classes.append(school_class)
        return school_classes

    def generate_subjects(self):
        # Example subjects for junior and senior classes
        junior_subjects = ['Mathematics', 'English', 'Basic Science', 'Social Studies']
        senior_subjects = ['Mathematics', 'English', 'Physics', 'Chemistry', 'Biology', 'Economics']
        subjects = []
        
        # Add junior subjects
        for subject_name in junior_subjects:
            subject, created = Subject.objects.get_or_create(
                name=subject_name,
                level='Junior',  # Specify the level
                defaults={
                    'code': f'{subject_name[:3].upper()}-JUN',  # Example: "MAT-JUN"
                    'description': f'{subject_name} for Junior level',
                }
            )
            subjects.append(subject)
        
        # Add senior subjects
        for subject_name in senior_subjects:
            subject, created = Subject.objects.get_or_create(
                name=subject_name,
                level='Senior',  # Specify the level
                defaults={
                    'code': f'{subject_name[:3].upper()}-SEN',  # Example: "MAT-SEN"
                    'description': f'{subject_name} for Senior level',
                }
            )
            subjects.append(subject)
        
        return subjects

    def generate_attendance(self, teacher, school_class, subject):
        attendance = AttendanceImage.objects.create(
            teacher=teacher,
            class_name=f'{school_class.level}{school_class.section}',  # Construct class name from `level` and `section`
            subject=subject.name,  # Assuming `subject` has a `name` field
            attendance_date=datetime.now() - timedelta(days=random.randint(0, 30)),
            uploaded_by=fake.name(),
            remarks=random.choice([
                "was on time",
                "was late to class",
                "didn't come at all",
                "left before time",
                "other"
            ])
        )
        return attendance