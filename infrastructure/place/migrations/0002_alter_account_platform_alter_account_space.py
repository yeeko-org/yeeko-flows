# Generated by Django 4.2.9 on 2024-07-05 15:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('service', '0001_initial'),
        ('place', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='account',
            name='platform',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to='service.platform'),
        ),
        migrations.AlterField(
            model_name='account',
            name='space',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='accounts', to='place.space'),
        ),
    ]