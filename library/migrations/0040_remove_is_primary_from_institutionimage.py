# Generated by Django 5.2 on 2025-06-13 16:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0039_institutionimage'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='institutionimage',
            options={'ordering': ['-created_at']},
        ),
        migrations.RemoveField(
            model_name='institutionimage',
            name='is_primary',
        ),
    ]
