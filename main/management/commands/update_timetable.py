from django.core.management.base import BaseCommand
from main.models import Timetable

class Command(BaseCommand):
    help = "Update the timetable schedule field for all records."

    def handle(self, *args, **kwargs):
        for timetable in Timetable.objects.all():
            schedule = {
                timetable.day: [
                    timetable.period_1 or "",
                    timetable.period_2 or "",
                    timetable.period_3 or "",
                    timetable.period_4 or "",
                    timetable.period_5 or "",
                    timetable.period_6 or "",
                    timetable.period_7 or "",
                    timetable.period_8 or "",
                    timetable.period_9 or ""
                ]
            }
            
            if hasattr(timetable, 'schedule'):
                timetable.schedule = schedule
                timetable.save()
                self.stdout.write(self.style.SUCCESS(f"Updated timetable for {timetable.day}"))
            else:
                self.stdout.write(self.style.WARNING(f"Skipping timetable for {timetable.day} - No 'schedule' field"))
