from django.core.management.base import BaseCommand
from your_app.models import Student, SchoolClass
from faker import Faker
import random

fake = Faker()

class Command(BaseCommand):
    help = 'Generate sample student data with guardian and parent details'

    def handle(self, *args, **kwargs):
        school_classes = list(SchoolClass.objects.all())  # Fetch all classes
        if not school_classes:
            self.stdout.write(self.style.WARNING("No school classes found! Add some classes first."))
            return

        for _ in range(10):  # Generate 10 students
            school_class = random.choice(school_classes)  # Assign a random class
           
            student = Student.objects.create(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                gender=random.choice(['M', 'F']),
                date_of_birth=fake.date_of_birth(minimum_age=10, maximum_age=18),
                admission_date=fake.date_this_decade(),
                school_class=school_class,
                residency_status=random.choice(['boarder', 'day']),
                fee_status=random.choice(['paid', 'unpaid']),
                guardian_name=fake.name(),
                guardian_phone=fake.phone_number(),
                guardian_email=fake.email(),
                parent_name=fake.name(),
                parent_phone=fake.phone_number(),
                parent_email=fake.email(),
            )

            self.stdout.write(self.style.SUCCESS(f"Created student: {student.first_name} {student.last_name}"))