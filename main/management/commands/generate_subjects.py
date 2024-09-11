from django.core.management.base import BaseCommand
from main.models import Subject, Teacher
from faker import Faker
import random

class Command(BaseCommand):
    help = 'Generates specific subjects for junior and senior levels with assigned teachers'

    def handle(self, *args, **options):
        faker = Faker()

        # Define specific subjects for junior and senior levels
        junior_subjects = [
            'Mathematics', 'English Language', 'Basic Science', 'Social Studies', 
            'Civic Education', 'Physical and Health Education', 'Computer Studies',
            'Agricultural Science', 'Business Studies', 'Home Economics'
        ]

        senior_subjects = [
            'Mathematics', 'English Language', 'Biology', 'Physics', 
            'Chemistry', 'Economics', 'Government', 'Geography', 
            'Literature in English', 'Further Mathematics'
        ]

        # Get all available teachers
        teachers = list(Teacher.objects.all())

        if not teachers:
            self.stdout.write(self.style.ERROR('No teachers available to assign'))
            return

        # Subject codes to ensure uniqueness
        used_codes = set()

        def generate_unique_code():
            while True:
                code = faker.bothify(text='??###').upper()
                if code not in used_codes:
                    used_codes.add(code)
                    return code

        # Create subjects for junior levels
        for name in junior_subjects:
            code = generate_unique_code()
            description = faker.sentence()
            random_teacher = random.choice(teachers)
            Subject.objects.create(name=name, level='Junior', code=code, description=description, teacher=random_teacher)

        # Create subjects for senior levels
        for name in senior_subjects:
            code = generate_unique_code()
            description = faker.sentence()
            random_teacher = random.choice(teachers)
            Subject.objects.create(name=name, level='Senior', code=code, description=description, teacher=random_teacher)

        self.stdout.write(self.style.SUCCESS(f'Successfully generated {len(junior_subjects)} junior and {len(senior_subjects)} senior subjects with assigned teachers'))
