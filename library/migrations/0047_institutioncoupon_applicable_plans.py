# Generated by Django 5.2 on 2025-06-16 16:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0046_institutionsubscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='institutioncoupon',
            name='applicable_plans',
            field=models.ManyToManyField(blank=True, help_text='Subscription plans this coupon can be applied to', to='library.institutionsubscriptionplan'),
        ),
    ]
