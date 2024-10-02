# Generated by Django 4.2.15 on 2024-09-27 09:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0019_alter_club_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='admissions',
            name='student_name',
        ),
        migrations.AddField(
            model_name='admissions',
            name='student',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='admissions', to='main.student'),
            preserve_default=False,
        ),
    ]
