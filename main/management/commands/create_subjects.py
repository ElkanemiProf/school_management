from django.core.management.base import BaseCommand
from main.models import Subject
import random
import string

class Command(BaseCommand):
    help = 'Creates subjects for junior and senior levels with unique codes'

    def generate_unique_code(self):
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
            if not Subject.objects.filter(code=code).exists():
                return code

    def handle(self, *args, **options):
        # List of junior and senior subjects
        junior_subjects = [
            'Mathematics', 'English Language', 'Basic Science', 'Social Studies',
            'Civic Education', 'Home Economics', 'Computer Studies', 'Agricultural Science'
        ]
        senior_subjects = [
            'Mathematics', 'English Language', 'Physics', 'Chemistry', 'Biology',
            'Government', 'Economics', 'Literature in English', 'Geography'
        ]
        
        # Create junior subjects
        for subject_name in junior_subjects:
            Subject.objects.create(
                name=subject_name,
                level='Junior',
                code=self.generate_unique_code()
            )

        # Create senior subjects
        for subject_name in senior_subjects:
            Subject.objects.create(
                name=subject_name,
                level='Senior',
                code=self.generate_unique_code()
            )

        self.stdout.write(self.style.SUCCESS(f'Successfully created {len(junior_subjects)} junior subjects and {len(senior_subjects)} senior subjects'))
