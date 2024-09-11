from django.core.management.base import BaseCommand
from faker import Faker
from main.models import Event, Student
import random
from datetime import timedelta
from django.utils import timezone

class Command(BaseCommand):
    help = 'Generate 10 different secondary school events'

    def handle(self, *args, **kwargs):
        fake = Faker()

        # List of example secondary school event names
        event_names = [
            "Science Fair",
            "Sports Day",
            "Art Exhibition",
            "Music Concert",
            "Debate Competition",
            "Cultural Festival",
            "Teachers' Day Celebration",
            "School Trip",
            "Graduation Ceremony",
            "Parents' Day"
        ]

        # Ensure there are students to participate in the events
        students = list(Student.objects.all())
        if not students:
            self.stdout.write(self.style.ERROR('No students found in the database! Please add students first.'))
            return

        for event_name in event_names:
            # Generate a random event date
            event_date = timezone.now() + timedelta(days=random.randint(1, 365))

            # Generate a random description
            description = fake.text()

            # Create an event
            event = Event.objects.create(
                name=event_name,
                date=event_date,
                description=description
            )

            # Randomly assign students to the event
            random_participants = random.sample(students, random.randint(5, len(students)))
            event.participants.set(random_participants)

            self.stdout.write(self.style.SUCCESS(f'Created event: {event_name}'))

        self.stdout.write(self.style.SUCCESS('Successfully created 10 secondary school events'))
