# Generated by Django 5.2 on 2025-04-29 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0015_alter_library_max_banners_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='check_in_color',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='attendance',
            name='check_out_color',
            field=models.IntegerField(default=0),
        ),
    ]
