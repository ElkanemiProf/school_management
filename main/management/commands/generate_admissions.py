from django.core.management.base import BaseCommand
from faker import Faker
import random
from main.models import Admissions, Student, SchoolClass
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Generates admissions data for the years 2020 to 2025, with 2025 admissions being all JS1 students'

    def handle(self, *args, **kwargs):
        fake = Faker()

        # Years to generate admissions for
        years = [2020, 2021, 2022, 2023, 2024, 2025]

        # Get all students and classes
        students = Student.objects.all()
        school_classes = SchoolClass.objects.all()

        if not students.exists() or not school_classes.exists():
            self.stdout.write(self.style.ERROR("No students or school classes found. Please create them first."))
            return

        for year in years:
            if year == 2025:
                # For 2025, generate admissions for all JS1 students
                js1_classes = SchoolClass.objects.filter(level='JS1')
                if not js1_classes.exists():
                    self.stdout.write(self.style.WARNING("No JS1 classes found. Skipping 2025 admissions."))
                    continue

                js1_students = Student.objects.filter(school_class__level='JS1')
                if not js1_students.exists():
                    self.stdout.write(self.style.WARNING("No JS1 students found. Skipping 2025 admissions."))
                    continue

                for student in js1_students:
                    # Generate a random admission date within 2025
                    admission_date = fake.date_between_dates(
                        date_start=datetime(2025, 1, 1),
                        date_end=datetime(2025, 12, 31)
                    )

                    # Set admission status to 'accepted' for JS1 students in 2025
                    admission_status = 'accepted'
                    admission_remarks = None

                    # Create the admission record
                    Admissions.objects.create(
                        student=student,
                        admission_date=admission_date,
                        admission_status=admission_status,
                        school_class=student.school_class,
                        admission_remarks=admission_remarks
                    )

                self.stdout.write(self.style.SUCCESS(f"Generated admissions for 2025 (all JS1 students)"))
            else:
                # For other years, generate random admissions
                for _ in range(random.randint(20, 50)):  # Generate 20-50 admissions per year
                    # Randomly select a student and school class
                    student = random.choice(students)
                    school_class = random.choice(school_classes)

                    # Generate a random admission date within the year
                    admission_date = fake.date_between_dates(
                        date_start=datetime(year, 1, 1),
                        date_end=datetime(year, 12, 31)
                    )

                    # Generate random admission status and remarks
                    admission_status = random.choice(['pending', 'accepted', 'rejected'])
                    admission_remarks = fake.text(max_nb_chars=200) if admission_status == 'rejected' else None

                    # Create the admission record
                    Admissions.objects.create(
                        student=student,
                        admission_date=admission_date,
                        admission_status=admission_status,
                        school_class=school_class,
                        admission_remarks=admission_remarks
                    )

                self.stdout.write(self.style.SUCCESS(f"Generated admissions for {year}"))

        self.stdout.write(self.style.SUCCESS("Admissions generation complete."))