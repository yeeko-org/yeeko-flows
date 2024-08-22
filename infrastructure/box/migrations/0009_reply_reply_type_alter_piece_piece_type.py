# Generated by Django 4.2.9 on 2024-07-25 03:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('box', '0008_alter_piece_piece_type_alter_template_raw_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='reply',
            name='reply_type',
            field=models.CharField(choices=[('payload', 'Payload'), ('quick_reply', 'Respuesta rápida'), ('url', 'URL')], default='payload', max_length=20),
        ),
        migrations.AlterField(
            model_name='piece',
            name='piece_type',
            field=models.CharField(choices=[('content', 'Contenido'), ('destinations', 'Para Destinos'), ('template', 'Template')], default='content', max_length=20),
        ),
    ]