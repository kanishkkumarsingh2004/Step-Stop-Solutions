# Generated by Django 5.2 on 2025-06-26 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0078_admincard_gym'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gym',
            name='contact_phone',
            field=models.JSONField(blank=True, default=list, help_text='A list of contact phone numbers.'),
        ),
    ]
