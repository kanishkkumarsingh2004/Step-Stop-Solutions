# Generated by Django 5.2 on 2025-04-27 22:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0012_usersubscription_end_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='accepted_privacy_policy',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customuser',
            name='accepted_terms',
            field=models.BooleanField(default=False),
        ),
    ]
