# Generated by Django 5.2 on 2025-06-23 16:33

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0065_alter_institutioncardlog_user_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CoachingAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('check_in_time', models.DateTimeField(blank=True, null=True)),
                ('check_out_time', models.DateTimeField(blank=True, null=True)),
                ('check_in_color', models.IntegerField(default=0)),
                ('check_out_color', models.IntegerField(default=0)),
                ('duration_color', models.IntegerField(default=0)),
                ('nfc_id', models.CharField(blank=True, max_length=100, null=True)),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='library.institution')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coaching_attendances', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'institution', 'check_in_time')},
            },
        ),
        migrations.CreateModel(
            name='LibraryAttendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('check_in_time', models.DateTimeField(blank=True, null=True)),
                ('check_out_time', models.DateTimeField(blank=True, null=True)),
                ('check_in_color', models.IntegerField(default=0)),
                ('check_out_color', models.IntegerField(default=0)),
                ('duration_color', models.IntegerField(default=0)),
                ('nfc_id', models.CharField(blank=True, max_length=100, null=True)),
                ('library', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='library.library')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='library_attendances', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'library', 'check_in_time')},
            },
        ),
        migrations.DeleteModel(
            name='Attendance',
        ),
    ]
