from django.core.management.base import BaseCommand
from faker import Faker
import random
from main.models import Student, SchoolClass  # Replace 'your_app' with the name of your app
from .nigerian_names import NigerianNamesProvider

class Command(BaseCommand):
    help = 'Generates students for all classes with Nigerian female names'

    def handle(self, *args, **kwargs):
        fake = Faker()
        fake.add_provider(NigerianNamesProvider)  # Add the custom provider

        classes = ['JS1A', 'JS1B', 'JS1C', 'JS1D',
                   'JS2A', 'JS2B', 'JS2C', 'JS2D',
                   'JS3A', 'JS3B', 'JS3C', 'JS3D',
                   'SS1A', 'SS1B', 'SS1C', 'SS1D',
                   'SS2A', 'SS2B', 'SS2C', 'SS2D',
                   'SS3A', 'SS3B', 'SS3C', 'SS3D']

        for class_name in classes:
            school_class, created = SchoolClass.objects.get_or_create(level=class_name[:-1], section=class_name[-1])

            num_students = random.randint(25, 35)

            for _ in range(num_students):
                first_name = fake.nigerian_female_name()
                last_name = fake.last_name()
                gender = 'female'
                residency_status = random.choice(['boarder', 'day_student'])

                Student.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    gender=gender,
                    school_class=school_class,
                    school_fees_status=random.choice(['paid', 'unpaid']),
                    residency_status=residency_status
                )

                self.stdout.write(self.style.SUCCESS(f"Created student {first_name} {last_name} in class {class_name}"))

        self.stdout.write(self.style.SUCCESS("Student generation complete."))
