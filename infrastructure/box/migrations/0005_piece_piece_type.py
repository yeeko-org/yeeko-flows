# Generated by Django 4.2.9 on 2024-06-10 15:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0004_rename_is_section_reply_is_header_section'),
    ]

    operations = [
        migrations.AddField(
            model_name='piece',
            name='piece_type',
            field=models.CharField(choices=[('content', 'Contenido'), ('destinations', 'Para Destinos')], default='content', max_length=20),
        ),
    ]