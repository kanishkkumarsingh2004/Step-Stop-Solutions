# Generated by Django 5.2 on 2025-05-01 09:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0020_library_available_seats_library_total_seats_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='library',
            name='total_seats',
        ),
    ]
