# Generated by Django 5.2 on 2025-06-20 14:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0056_timetable_class_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimetableEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(max_length=10)),
                ('session', models.CharField(max_length=20)),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('subject', models.CharField(max_length=100)),
                ('faculty_ssid', models.CharField(max_length=20)),
                ('faculty_name', models.CharField(blank=True, max_length=100, null=True)),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='library.institution')),
            ],
        ),
        migrations.DeleteModel(
            name='Timetable',
        ),
    ]
