# Generated by Django 5.2 on 2025-06-13 07:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0031_remove_institution_capacity_institution_classrooms'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='institution',
            name='institution_type',
        ),
    ]
