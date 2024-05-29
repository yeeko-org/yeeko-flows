# Generated by Django 4.2.9 on 2024-05-28 18:41

from django.db import migrations, models
import django.db.models.deletion
import infrastructure.place.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('service', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Space',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=180)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('bot_name', models.CharField(blank=True, default='Xico', max_length=40, null=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='spaces')),
                ('test', models.BooleanField(default=False)),
                ('params', models.JSONField(blank=True, default=infrastructure.place.models.default_params, null=True)),
            ],
            options={
                'verbose_name': 'Espacio (Página)',
                'verbose_name_plural': 'Espacios (Páginas)',
            },
        ),
        migrations.CreateModel(
            name='Account',
            fields=[
                ('pid', models.CharField(max_length=191, primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, max_length=180, null=True)),
                ('token', models.CharField(blank=True, max_length=255, null=True)),
                ('config', models.JSONField(blank=True, default=infrastructure.place.models.default_params, null=True)),
                ('active', models.BooleanField(default=True)),
                ('init_text_response', models.BooleanField(default=True)),
                ('text_response', models.BooleanField(default=True)),
                ('payload_response', models.BooleanField(default=True)),
                ('notif_enabled', models.BooleanField(default=True)),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='service.platform')),
                ('space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='place.space')),
            ],
            options={
                'verbose_name': 'Cuenta por plataforma',
                'verbose_name_plural': 'Cuentas por plataforma',
            },
        ),
    ]
