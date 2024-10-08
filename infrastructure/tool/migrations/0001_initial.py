# Generated by Django 4.2.9 on 2024-05-31 07:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('place', '0001_initial'),
        ('service', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Behavior',
            fields=[
                ('name', models.CharField(max_length=80, primary_key=True, serialize=False)),
                ('can_piece', models.BooleanField(default=True)),
                ('can_destination', models.BooleanField(default=True)),
                ('in_code', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Función',
                'verbose_name_plural': 'Funciones',
            },
        ),
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80)),
                ('public_name', models.CharField(blank=True, max_length=80, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_required', models.BooleanField(default=False)),
                ('default_value', models.CharField(blank=True, max_length=255, null=True)),
                ('data_type', models.CharField(choices=[('integer', 'Número'), ('string', 'Texto'), ('boolean', 'Booleano'), ('json', 'JSON'), ('any', 'Cualquiera'), ('foreign_key', 'Llave Foránea')], max_length=20)),
                ('customizable_by_piece', models.BooleanField(default=False)),
                ('addl_config', models.JSONField(blank=True, null=True)),
                ('rules', models.JSONField(blank=True, null=True)),
                ('model', models.CharField(blank=True, choices=[('piece', 'Piece'), ('fragment', 'Fragment'), ('yeekonsult', 'Yeeko'), ('reply', 'Reply')], max_length=20, null=True)),
                ('order', models.IntegerField(default=40)),
                ('addl_dashboard', models.JSONField(blank=True, null=True)),
                ('deleted', models.BooleanField(default=False)),
                ('behavior', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tool.behavior')),
            ],
            options={
                'verbose_name': 'Parámetro',
                'verbose_name_plural': 'Parámetros',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('name', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('public_name', models.CharField(blank=True, max_length=80, null=True)),
                ('is_custom', models.BooleanField(default=False)),
                ('open_available', models.BooleanField(default=True)),
                ('app_label', models.CharField(blank=True, max_length=50, null=True)),
                ('spaces', models.ManyToManyField(blank=True, to='place.space')),
            ],
            options={
                'verbose_name': 'Colección',
                'verbose_name_plural': 'Colecciones',
            },
        ),
        migrations.AddField(
            model_name='behavior',
            name='collection',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tool.collection'),
        ),
        migrations.AddField(
            model_name='behavior',
            name='interaction_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='service.interactiontype'),
        ),
    ]
