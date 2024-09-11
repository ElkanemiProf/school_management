from django.core.management.base import BaseCommand
from main.models import SchoolClass

class Command(BaseCommand):
    help = 'Creates missing school classes (JS1A - SS3D)'

    def handle(self, *args, **options):
        levels = ['JS1', 'JS2', 'JS3', 'SS1', 'SS2', 'SS3']
        sections = ['A', 'B', 'C', 'D']

        for level in levels:
            for section in sections:
                school_class, created = SchoolClass.objects.get_or_create(level=level, section=section)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Created {school_class.level} {school_class.section}'))
                else:
                    self.stdout.write(self.style.WARNING(f'{school_class.level} {school_class.section} already exists'))
