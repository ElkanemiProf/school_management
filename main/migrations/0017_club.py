# Generated by Django 4.2.15 on 2024-09-24 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_admissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Club',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('students', models.ManyToManyField(related_name='clubs', to='main.student')),
                ('teachers', models.ManyToManyField(related_name='clubs', to='main.teacher')),
            ],
        ),
    ]
