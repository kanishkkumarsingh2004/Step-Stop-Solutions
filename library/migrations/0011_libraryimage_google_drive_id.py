# Generated by Django 5.2 on 2025-04-27 08:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0010_libraryimage'),
    ]

    operations = [
        migrations.AddField(
            model_name='libraryimage',
            name='google_drive_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
