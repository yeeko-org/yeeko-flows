# Generated by Django 4.2.9 on 2024-08-03 05:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0013_alter_platformtemplate_piece_templateparameter'),
    ]

    operations = [
        migrations.AddField(
            model_name='templateparameter',
            name='component_type',
            field=models.CharField(choices=[('body', 'Body'), ('header', 'Header'), ('footer', 'Footer')], default='body', max_length=10),
        ),
        migrations.AddField(
            model_name='templateparameter',
            name='order',
            field=models.SmallIntegerField(default=0),
        ),
    ]
