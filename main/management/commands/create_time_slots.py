from datetime import time, timedelta, datetime
from django.core.management.base import BaseCommand
from main.models import TimeSlot

class Command(BaseCommand):
    help = 'Create time slots for the timetable'

    def handle(self, *args, **kwargs):
        # Define the time slots, starting from 8:00 AM and ending at 2:40 PM
        start_time = time(8, 0)
        end_time = time(14, 40)
        period_duration = timedelta(minutes=40)

        # Assembly days (Monday, Wednesday, and Friday)
        assembly_days = ['Monday', 'Wednesday', 'Friday']

        # Break time from 11:00 AM to 11:40 AM
        break_start_time = time(11, 0)
        break_end_time = time(11, 40)

        def create_time_slots():
            # Loop through each day of the school week
            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                current_time = start_time
                while current_time < end_time:
                    next_time = (datetime.combine(datetime.today(), current_time) + period_duration).time()

                    # Add assembly for Monday, Wednesday, and Friday at 8:00 AM to 8:40 AM
                    if current_time == time(8, 0) and day in assembly_days:
                        TimeSlot.objects.create(day_of_week=day, start_time=current_time, end_time=next_time, is_assembly=True)
                    # Add break time from 11:00 AM to 11:40 AM
                    elif current_time == break_start_time:
                        TimeSlot.objects.create(day_of_week=day, start_time=break_start_time, end_time=break_end_time, is_break=True)
                    # Create regular class periods
                    else:
                        TimeSlot.objects.create(day_of_week=day, start_time=current_time, end_time=next_time)

                    # Move to the next time slot
                    current_time = next_time

        # Call the function to create the time slots
        create_time_slots()

        # Output success message to the terminal
        self.stdout.write(self.style.SUCCESS('Successfully created time slots'))
