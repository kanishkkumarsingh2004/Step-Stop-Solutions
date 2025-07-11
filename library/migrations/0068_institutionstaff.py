# Generated by Django 5.2 on 2025-06-24 13:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0067_alter_institutioncardlog_unique_together_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstitutionStaff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permissions', models.CharField(blank=True, help_text='Comma-separated list of permission keys.', max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff', to='library.institution')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff_in_institutions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'unique_together': {('institution', 'user')},
            },
        ),
    ]
