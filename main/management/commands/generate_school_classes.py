from django.core.management.base import BaseCommand
from faker import Faker
from main.models import SchoolClass
import random

class Command(BaseCommand):
    help = 'Generate random school classes'

    def handle(self, *args, **options):
        faker = Faker()
        levels = ['JS1', 'JS2', 'JS3', 'SS1', 'SS2', 'SS3']
        sections = ['A', 'B', 'C', 'D']

        # Generate 10 random school classes
        for _ in range(10):
            level = random.choice(levels)
            section = random.choice(sections)
            # Ensure unique combination of level and section
            if not SchoolClass.objects.filter(level=level, section=section).exists():
                SchoolClass.objects.create(level=level, section=section)
                print(f'Created School Class: {level} {section}')
            else:
                print(f'School Class {level} {section} already exists')

        self.stdout.write(self.style.SUCCESS('Successfully generated school classes'))
