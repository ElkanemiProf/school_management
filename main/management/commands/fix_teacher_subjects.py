from django.core.management.base import BaseCommand
from main.models import Teacher, Subject

class Command(BaseCommand):
    help = "Ensures teachers and subjects are properly linked"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Updating teacher-subject relationships..."))

        # Step 1: Fix teacher -> subject relationship
        for teacher in Teacher.objects.all():
            for subject in teacher.subject_taught.all():
                if teacher not in subject.teachers.all():
                    subject.teachers.add(teacher)

        # Step 2: Fix subject -> teacher relationship
        for subject in Subject.objects.all():
            for teacher in subject.teachers.all():
                if subject not in teacher.subject_taught.all():
                    teacher.subject_taught.add(subject)

        # Step 3: Assign teachers to unassigned subjects based on level
        unassigned_subjects = Subject.objects.filter(teachers__isnull=True)
        for subject in unassigned_subjects:
            possible_teachers = Teacher.objects.filter(subject_taught__level=subject.level)
            if possible_teachers.exists():
                subject.teachers.add(*possible_teachers)
                self.stdout.write(self.style.SUCCESS(f"Auto-assigned teachers to {subject.name} ({subject.level})"))
            else:
                self.stdout.write(self.style.ERROR(f"No teachers found for {subject.name} ({subject.level})!"))

        self.stdout.write(self.style.SUCCESS("Teacher-subject relationships updated successfully!"))

        # Summary Report
        for subject in Subject.objects.all():
            teacher_count = subject.teachers.count()
            self.stdout.write(f"{subject.name} ({subject.level}): {teacher_count} teacher(s)")

        self.stdout.write(self.style.SUCCESS("Done!"))
