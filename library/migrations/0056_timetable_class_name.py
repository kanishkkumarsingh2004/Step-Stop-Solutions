# Generated by Django 5.2 on 2025-06-19 18:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0055_timetable'),
    ]

    operations = [
        migrations.AddField(
            model_name='timetable',
            name='class_name',
            field=models.CharField(default=11, max_length=100),
            preserve_default=False,
        ),
    ]
