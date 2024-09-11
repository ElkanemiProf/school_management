from django.core.management.base import BaseCommand
from faker import Faker
from main.models import Student, Grade, Subject, SchoolClass
import random

class Command(BaseCommand):
    help = 'Generate random grades for students based on their class level'

    JUNIOR_SUBJECTS = [
        {'name': 'Math', 'code': 'MTH-JS'},
        {'name': 'English', 'code': 'ENG-JS'},
        {'name': 'Basic Science', 'code': 'SCI-JS'},
        {'name': 'Social Studies', 'code': 'SOC-JS'},
        {'name': 'Agricultural Science', 'code': 'AGR-JS'}
    ]
    
    SENIOR_SUBJECTS = [
        {'name': 'Physics', 'code': 'PHY-SS'},
        {'name': 'Chemistry', 'code': 'CHE-SS'},
        {'name': 'Biology', 'code': 'BIO-SS'},
        {'name': 'Mathematics', 'code': 'MTH-SS'},
        {'name': 'English', 'code': 'ENG-SS'},
        {'name': 'Geography', 'code': 'GEO-SS'}
    ]
    
    def handle(self, *args, **options):
        faker = Faker()

        # Fetch all students
        students = Student.objects.all()

        for student in students:
            # Determine if the student is in junior or senior secondary
            student_class = student.school_class.level
            if student_class.startswith('JS'):  # Junior secondary
                subjects = self.JUNIOR_SUBJECTS
            else:  # Senior secondary (SS)
                subjects = self.SENIOR_SUBJECTS

            # Assign grades for each subject
            for subject_info in subjects:
                # Get or create the subject, ensuring unique code
                subject, created = Subject.objects.get_or_create(
                    name=subject_info['name'],
                    code=subject_info['code']
                )
                
                # Randomly generate a grade (A, B, C, D, E, F)
                grade_letter = random.choice(['A', 'B', 'C', 'D', 'E', 'F'])
                
                # Create the grade record
                Grade.objects.create(
                    student=student,
                    subject=subject,
                    term='First Term',  # Adjust as needed
                    score=random.uniform(40, 100),  # Random score between 40 and 100
                    grade=grade_letter
                )
                
                print(f'Assigned grade {grade_letter} for {subject.name} to {student.first_name} {student.last_name}')

        self.stdout.write(self.style.SUCCESS('Successfully generated grades for all students'))
