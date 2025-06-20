# Generated by Django 5.2 on 2025-06-17 12:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0050_paymentverification'),
    ]

    operations = [
        migrations.CreateModel(
            name='InstitutionExpense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=255)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date', models.DateField()),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('institution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to='library.institution')),
            ],
            options={
                'verbose_name': 'Institution Expense',
                'verbose_name_plural': 'Institution Expenses',
                'ordering': ['-date', '-created_at'],
            },
        ),
    ]
