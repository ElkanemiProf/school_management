# Generated by Django 4.2.15 on 2024-09-19 10:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_alter_note_options_alter_note_content'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='note',
            name='timestamp',
        ),
    ]
