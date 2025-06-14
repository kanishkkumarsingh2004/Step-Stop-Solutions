# Generated by Django 5.2 on 2025-06-13 07:33

import shortuuid.django_fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0032_remove_institution_institution_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='uid',
            field=shortuuid.django_fields.ShortUUIDField(alphabet='123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjklmnpqrstuvwxyz', length=20, max_length=20, prefix='', unique=True),
        ),
    ]
