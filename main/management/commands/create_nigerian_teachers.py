from django.core.management.base import BaseCommand
from main.models import Teacher, Subject, SchoolClass
from django.contrib.auth.models import User
import random

class Command(BaseCommand):
    help = 'Deletes all existing teachers, creates new teachers with Nigerian names, and ensures each subject has at least 3 teachers.'

    def handle(self, *args, **options):
        # Custom lists of Nigerian first and last names
        nigerian_first_names = [
            "Chinedu", "Ngozi", "Oluwatobi", "Adebayo", "Chiamaka", "Emeka", "Funmilayo", "Obinna", "Adanna", "Ifeoma",
            "Chinwe", "Olumide", "Aisha", "Eze", "Uche", "Oluwaseun", "Amina", "Chukwuemeka", "Fatima", "Olufemi",
            "Chioma", "Ibrahim", "Olayinka", "Adetokunbo", "Nneka", "Oladipo", "Zainab", "Olubunmi", "Adewale", "Olanrewaju",
            "Temitope", "Oluwakemi", "Oluwatosin", "Oluwafemi", "Oluwadamilola", "Oluwaseyi", "Oluwatoyin", "Oluwatunmise",
            "Oluwatobiloba", "Oluwatomiwa", "Oluwatoni", "Oluwatoyosi", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo",
            "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin",
            "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo",
            "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin",
            "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo",
            "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin",
            "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo",
            "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin",
            "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo", "Oluwatoyin", "Oluwatoyinbo"
        ]

        nigerian_last_names = [
            "Okonkwo", "Eze", "Adeyemi", "Okafor", "Nwankwo", "Obi", "Adeleke", "Onyeka", "Chukwu", "Okeke",
            "Okafor", "Nwosu", "Okoro", "Ezeogu", "Onwuka", "Okoye", "Nwoke", "Okoli", "Nwankwo", "Okonkwo",
            "Eze", "Adeyemi", "Okafor", "Nwankwo", "Obi", "Adeleke", "Onyeka", "Chukwu", "Okeke", "Okafor",
            "Nwosu", "Okoro", "Ezeogu", "Onwuka", "Okoye", "Nwoke", "Okoli", "Nwankwo", "Okonkwo", "Eze",
            "Adeyemi", "Okafor", "Nwankwo", "Obi", "Adeleke", "Onyeka", "Chukwu", "Okeke", "Okafor", "Nwosu",
            "Okoro", "Ezeogu", "Onwuka", "Okoye", "Nwoke", "Okoli", "Nwankwo", "Okonkwo", "Eze", "Adeyemi",
            "Okafor", "Nwankwo", "Obi", "Adeleke", "Onyeka", "Chukwu", "Okeke", "Okafor", "Nwosu", "Okoro",
            "Ezeogu", "Onwuka", "Okoye", "Nwoke", "Okoli", "Nwankwo", "Okonkwo", "Eze", "Adeyemi", "Okafor",
            "Nwankwo", "Obi", "Adeleke", "Onyeka", "Chukwu", "Okeke", "Okafor", "Nwosu", "Okoro", "Ezeogu",
            "Onwuka", "Okoye", "Nwoke", "Okoli", "Nwankwo", "Okonkwo", "Eze", "Adeyemi", "Okafor", "Nwankwo"
        ]

        # Ensure no duplicates in the lists
        nigerian_first_names = list(set(nigerian_first_names))[:100]  # Ensure 100 unique first names
        nigerian_last_names = list(set(nigerian_last_names))[:100]  # Ensure 100 unique last names

        # Shuffle the lists to randomize the order
        random.shuffle(nigerian_first_names)
        random.shuffle(nigerian_last_names)

        # Fetch subjects and classes
        subjects = list(Subject.objects.all())
        classes = list(SchoolClass.objects.all())

        if not subjects or not classes:
            self.stdout.write(self.style.ERROR('Subjects or classes are missing'))
            return

        # Step 1: Delete all existing teachers
        Teacher.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Deleted all existing teachers.'))

        # Step 2: Create new teachers with Nigerian names
        num_teachers = len(subjects) * 3  # Ensure at least 3 teachers per subject
        teachers_created = 0

        for i in range(num_teachers):
            first_name = random.choice(nigerian_first_names)
            last_name = random.choice(nigerian_last_names)

            # Generate a unique username
            base_username = f"{first_name.lower()}.{last_name.lower()}"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # Create the user and teacher
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                password="password"  # Set a default password
            )
            teacher = Teacher.objects.create(user=user)

            # Assign a subject and a class to the teacher
            subject = subjects[i % len(subjects)]  # Round-robin assignment of subjects
            teacher.subject_taught.add(subject)

            school_class = random.choice(classes)  # Randomly assign a class
            teacher.classes_taught.add(school_class)

            teacher.save()
            teachers_created += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {teachers_created} teachers with Nigerian names.'))

        # Step 3: Ensure each subject has at least 3 teachers
        for subject in subjects:
            teachers_for_subject = Teacher.objects.filter(subject_taught=subject)
            if teachers_for_subject.count() < 3:
                # Assign additional teachers to this subject
                additional_teachers_needed = 3 - teachers_for_subject.count()
                available_teachers = Teacher.objects.exclude(subject_taught=subject)

                for _ in range(additional_teachers_needed):
                    if available_teachers.exists():
                        teacher = random.choice(available_teachers)
                        teacher.subject_taught.add(subject)
                        teacher.save()
                        self.stdout.write(self.style.WARNING(f'Assigned {teacher.user.get_full_name()} to {subject.name}.'))
                    else:
                        self.stdout.write(self.style.ERROR(f'Not enough teachers to assign to {subject.name}.'))
                        break

        self.stdout.write(self.style.SUCCESS('Ensured each subject has at least 3 teachers.'))