# Generated by Django 5.2 on 2025-04-26 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0005_attendance_nfc_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='library',
            name='recipient_name',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='library',
            name='thank_you_message',
            field=models.CharField(default=1, max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='library',
            name='upi_id',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
    ]
