# Generated by Django 4.2.9 on 2024-06-03 03:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reply',
            name='destination',
        ),
    ]