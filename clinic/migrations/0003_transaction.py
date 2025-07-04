# Generated by Django 5.2.1 on 2025-06-20 03:24

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0002_medicine_shelf_location'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('REQUEST', 'Medicine Request'), ('APPROVE', 'Request Approved'), ('REJECT', 'Request Rejected'), ('RESTOCK', 'Medicine Restocked')], max_length=10)),
                ('quantity', models.IntegerField()),
                ('notes', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('medicine', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='clinic.medicine')),
                ('patient', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='clinic.patient')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
