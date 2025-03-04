from django.core.management.base import BaseCommand
from main.models import Student, SchoolClass
from faker import Faker
import random

# Initialize Faker
fake = Faker()

# Define Nigerian names manually
nigerian_first_names_male = [
    "Chinedu", "Emeka", "Olumide", "Tunde", "Abdul", "Ibrahim", "Musa", "Sani", "Yusuf", "Oluwatobi"
]

nigerian_first_names_female = [
    "Aisha", "Chioma", "Funke", "Ngozi", "Amina", "Halima", "Zainab", "Fatima", "Adesuwa", "Oluwatoyin"
]

nigerian_last_names = [
    "Okonkwo", "Adeyemi", "Okafor", "Mohammed", "Ibrahim", "Nwankwo", "Obi", "Eze", "Balogun", "Suleiman"
]

class Command(BaseCommand):
    help = 'Generate sample student data with guardian and parent details for all levels and sections'

    def handle(self, *args, **kwargs):
        # Delete all existing students
        Student.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Deleted all existing students."))

        # Fetch all school classes (e.g., JS1-A, JS1-B, SS1-C, etc.)
        school_classes = list(SchoolClass.objects.all())
        if not school_classes:
            self.stdout.write(self.style.WARNING("No school classes found! Add some classes first."))
            return

        for school_class in school_classes:
            # Generate a random number of students between 30 and 40 for each class
            total_students = random.randint(30, 40)

            # Ensure the number of male and female students is balanced
            # Male students should be between 10 and (total_students - 10)
            male_students = random.randint(10, total_students - 10)
            female_students = total_students - male_students

            self.stdout.write(self.style.SUCCESS(
                f"Generating {total_students} students for {school_class.level} {school_class.section}: "
                f"{male_students} males and {female_students} females"
            ))

            # Generate male students
            for _ in range(male_students):
                first_name = random.choice(nigerian_first_names_male)
                last_name = random.choice(nigerian_last_names)

                student = Student.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    gender='male',
                    date_of_birth=fake.date_of_birth(minimum_age=10, maximum_age=18),
                    admission_date=fake.date_this_decade(),
                    school_class=school_class,
                    residency_status=random.choice(['boarder', 'day_student']),
                    school_fees_status=random.choice(['paid', 'unpaid']),
                    guardians_name=fake.name(),
                    guardians_phone_number=fake.phone_number(),
                    parents_name=fake.name(),
                    parents_phone_number=fake.phone_number(),
                )

                self.stdout.write(self.style.SUCCESS(
                    f"Created male student: {student.first_name} {student.last_name} in {school_class.level} {school_class.section}"
                ))

            # Generate female students
            for _ in range(female_students):
                first_name = random.choice(nigerian_first_names_female)
                last_name = random.choice(nigerian_last_names)

                student = Student.objects.create(
                    first_name=first_name,
                    last_name=last_name,
                    gender='female',
                    date_of_birth=fake.date_of_birth(minimum_age=10, maximum_age=18),
                    admission_date=fake.date_this_decade(),
                    school_class=school_class,
                    residency_status=random.choice(['boarder', 'day_student']),
                    school_fees_status=random.choice(['paid', 'unpaid']),
                    guardians_name=fake.name(),
                    guardians_phone_number=fake.phone_number(),
                    parents_name=fake.name(),
                    parents_phone_number=fake.phone_number(),
                )

                self.stdout.write(self.style.SUCCESS(
                    f"Created female student: {student.first_name} {student.last_name} in {school_class.level} {school_class.section}"
                ))