# from django.core.management.base import BaseCommand
# from main.models import Subject, Teacher, SchoolClass
# import random

# class Command(BaseCommand):
#     help = 'Assigns unique teachers to subjects and classes without overlap'

#     def handle(self, *args, **options):
#         # Fetch all teachers and shuffle them for randomness
#         teachers = list(Teacher.objects.all())
#         random.shuffle(teachers)

#         # Fetch subjects with no teacher assigned
#         subjects_without_teachers = list(Subject.objects.filter(teacher__isnull=True))
#         random.shuffle(subjects_without_teachers)

#         if not teachers:
#             self.stdout.write(self.style.ERROR('No teachers available to assign'))
#             return

#         if not subjects_without_teachers:
#             self.stdout.write(self.style.ERROR('No subjects without teachers'))
#             return

#         # Assign each teacher to one subject if available
#         for teacher, subject in zip(teachers, subjects_without_teachers):
#             subject.teacher = teacher
#             subject.save()
#             self.stdout.write(self.style.SUCCESS(f'Assigned {teacher} to {subject}'))

#         # Fetch all classes and shuffle them for randomness
#         classes = list(SchoolClass.objects.all())
#         random.shuffle(classes)

#         # Ensure each teacher gets a unique class
#         for teacher in teachers:
#             if not classes:
#                 break  # If there are no more classes, stop assigning
#             random_class = classes.pop()  # Assign a unique class to each teacher
#             teacher.classes_taught.add(random_class)
#             teacher.save()
#             self.stdout.write(self.style.SUCCESS(f'Assigned {teacher} to class {random_class}'))

#         self.stdout.write(self.style.SUCCESS('All assignments are complete!'))


from django.core.management.base import BaseCommand
from django.db.models import Count
from main.models import Subject, Teacher, SchoolClass
import random

class Command(BaseCommand):
    help = 'Assigns random teachers to subjects without a teacher and assigns random classes to teachers'

    def handle(self, *args, **options):
        # Fetch all teachers
        teachers = list(Teacher.objects.all())
        
        # Fetch subjects with no teacher assigned
        subjects_without_teachers = Subject.objects.filter(teacher__isnull=True)
        
        if not teachers:
            self.stdout.write(self.style.ERROR('No teachers available to assign'))
            return
        
        # Fetch all classes
        classes = list(SchoolClass.objects.all())

        if not classes:
            self.stdout.write(self.style.ERROR('No classes available to assign'))
            return
        
        # Randomly assign teachers to subjects and classes
        for subject in subjects_without_teachers:
            random_teacher = random.choice(teachers)
            subject.teacher = random_teacher
            subject.save()

            # Assign the same teacher to a random class
            random_class = random.choice(classes)
            random_teacher.classes_taught.add(random_class)
            random_teacher.save()

        self.stdout.write(self.style.SUCCESS(f'Assigned teachers to {subjects_without_teachers.count()} subjects and assigned random classes to those teachers'))

