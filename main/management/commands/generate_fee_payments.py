from django.core.management.base import BaseCommand
from faker import Faker
from main.models import Student, FeePayment
import random

class Command(BaseCommand):
    help = 'Generate random fee payments for students'

    def handle(self, *args, **options):
        faker = Faker()
        students = Student.objects.all()  # Fetch all students
        fee_amount = 50000.00  # Example fixed fee amount

        for student in students:
            # Randomly decide if the student has paid or not
            paid_status = random.choice(['Paid', 'Unpaid'])
            if paid_status == 'Paid':
                FeePayment.objects.create(
                    student=student,
                    amount_paid=fee_amount,
                    payment_date=faker.past_date(),
                    status=paid_status
                )
            else:
                FeePayment.objects.create(
                    student=student,
                    amount_paid=0,  # No amount paid
                    payment_date=None,  # No payment date for unpaid fees
                    status=paid_status
                )

            print(f'Fee payment status for {student.first_name} {student.last_name}: {paid_status}')

        self.stdout.write(self.style.SUCCESS('Successfully generated fee payment data for all students'))
