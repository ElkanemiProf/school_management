from django.core.management.base import BaseCommand
from faker import Faker
from main.models import Budget
import random

class Command(BaseCommand):
    help = 'Create dummy secondary school budget entries'

    def add_arguments(self, parser):
        parser.add_argument('total', type=int, help='Indicates the number of budgets to create')

    def handle(self, *args, **kwargs):
        fake = Faker()
        total = kwargs['total']

        # Define school-related categories
        school_categories = [
            "Science Department",
            "Sports Equipment",
            "Library",
            "Classroom Supplies",
            "School Trips",
            "IT Equipment",
            "Laboratory Equipment",
            "Teacher Training",
            "Student Welfare",
            "School Maintenance",
            "Cafeteria",
            "School Events",
        ]

        for _ in range(total):
            category = random.choice(school_categories)  # Randomly select a school-related category
            allocated_amount = round(random.uniform(1000, 10000), 2)
            spent_amount = round(random.uniform(0, allocated_amount), 2)
            description = fake.sentence(nb_words=10)  # Generate a random description

            # Create and save the Budget object
            budget = Budget(
                category=category,
                allocated_amount=allocated_amount,
                spent_amount=spent_amount,
                description=description
            )
            budget.save()

        self.stdout.write(self.style.SUCCESS(f'Successfully created {total} school budgets'))
