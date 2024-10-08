# Generated by Django 4.2.9 on 2024-05-31 07:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('place', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CrateType',
            fields=[
                ('name', models.CharField(max_length=120, primary_key=True, serialize=False)),
                ('public_name', models.CharField(blank=True, max_length=120, null=True)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Tipo de Contenedor (campaña)',
                'verbose_name_plural': 'Tipos de Contenedor (campaña)',
            },
        ),
        migrations.CreateModel(
            name='Flow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True, null=True)),
                ('has_definitions', models.BooleanField(default=False)),
                ('deleted', models.BooleanField(default=False)),
                ('space', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='place.space')),
            ],
            options={
                'verbose_name': 'Flujo Conversacional',
                'verbose_name_plural': 'Flujos Conversacionales',
                'unique_together': {('name', 'space')},
            },
        ),
        migrations.CreateModel(
            name='Crate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('description', models.TextField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('has_templates', models.BooleanField(default=False)),
                ('crate_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='flow.cratetype')),
                ('flow', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='flow.flow')),
            ],
            options={
                'verbose_name': 'Contenedor (campaña)',
                'verbose_name_plural': 'Contenedores (campañas)',
                'unique_together': {('name', 'crate_type')},
            },
        ),
    ]
