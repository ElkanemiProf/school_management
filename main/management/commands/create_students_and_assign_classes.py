from django.core.management.base import BaseCommand
from faker import Faker
from main.models import Student, SchoolClass

class Command(BaseCommand):
    help = 'Generate new students and assign them to classes with a minimum of 15 and a maximum of 25 students per class'

    def handle(self, *args, **options):
        faker = Faker()
        
        # Fetch all classes and count the number of students in each class
        all_classes = list(SchoolClass.objects.all())
        class_student_counts = {school_class: school_class.students.count() for school_class in all_classes}

        # Set the minimum and maximum number of students per class
        min_students = 15
        max_students = 25

        # Continue creating students until all classes have at least min_students
        while any(count < min_students for count in class_student_counts.values()):
            for school_class, count in class_student_counts.items():
                if count < min_students:
                    # Create a new student
                    first_name = faker.first_name_female()  # Assuming it's a girls' school
                    last_name = faker.last_name()
                    date_of_birth = faker.date_of_birth(minimum_age=10, maximum_age=18)
                    admission_date = faker.date_this_decade()

                    student = Student.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        gender='female',  # Assuming a girls' school
                        date_of_birth=date_of_birth,
                        admission_date=admission_date,
                        school_class=school_class
                    )

                    # Update the count for this class
                    class_student_counts[school_class] += 1
                    self.stdout.write(self.style.SUCCESS(f'Created and assigned {student.first_name} {student.last_name} to {school_class.level} {school_class.section}'))
                
                # Stop adding students to this class if it reaches the maximum limit
                if class_student_counts[school_class] >= max_students:
                    continue

        self.stdout.write(self.style.SUCCESS('Completed generating and assigning new students to classes.'))
