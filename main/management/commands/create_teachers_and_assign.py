from django.core.management.base import BaseCommand
from main.models import Teacher, Subject, SchoolClass
from django.contrib.auth.models import User
import random
from faker import Faker

class Command(BaseCommand):
    help = 'Creates teachers and assigns subjects and classes properly'

    def handle(self, *args, **options):
        fake = Faker()
        subjects = list(Subject.objects.all())
        classes = list(SchoolClass.objects.all())

        if not subjects or not classes:
            self.stdout.write(self.style.ERROR('Subjects or classes are missing'))
            return

        num_teachers = len(subjects)

        for i in range(num_teachers):
            first_name = fake.first_name_female()  # Generating a female first name
            last_name = fake.last_name()

            # Create the user and teacher
            user = User.objects.create_user(username=f"{first_name.lower()}.{last_name.lower()}",
                                            first_name=first_name,
                                            last_name=last_name,
                                            password="password")  # Set a default password or use a more secure method
            teacher = Teacher.objects.create(user=user)

            # Assign a subject and a class to the teacher
            subject = subjects[i % len(subjects)]
            teacher.subject_taught.add(subject)

            school_class = classes[i % len(classes)]
            teacher.classes_taught.add(school_class)

            teacher.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully created and assigned {num_teachers} teachers.'))
