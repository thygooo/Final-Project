# Generated by Django 5.2.1 on 2025-06-20 02:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicine',
            name='shelf_location',
            field=models.CharField(choices=[('Shelf 1', 'Shelf 1'), ('Shelf 2', 'Shelf 2'), ('Shelf 3', 'Shelf 3'), ('Shelf 4', 'Shelf 4')], default='Shelf 1', max_length=10),
        ),
    ]
