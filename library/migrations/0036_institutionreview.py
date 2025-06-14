# Generated by Django 5.2 on 2025-06-13 11:42

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0035_institution_city_institution_district_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstitutionReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveSmallIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])),
                ('comment', models.TextField(blank=True, null=True)),
                ('reply', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='library.institution')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
