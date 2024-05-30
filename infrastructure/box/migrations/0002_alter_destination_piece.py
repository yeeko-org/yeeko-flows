# Generated by Django 4.2.9 on 2024-05-30 02:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='destination',
            name='piece',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='destinations', to='box.piece'),
        ),
    ]