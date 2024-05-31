# Generated by Django 4.2.9 on 2024-05-31 07:53

from django.db import migrations, models
import django.db.models.deletion
import infrastructure.box.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('xtra', '0001_initial'),
        ('flow', '0001_initial'),
        ('tool', '0001_initial'),
        ('place', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Destination',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('destination_type', models.CharField(choices=[('url', 'URL'), ('behavior', 'Función Behavior'), ('piece', 'Pieza')], max_length=20, verbose_name='Tipo de destino')),
                ('url', models.CharField(blank=True, max_length=255, null=True, verbose_name='URL')),
                ('addl_params', models.JSONField(blank=True, null=True)),
                ('is_default', models.BooleanField(default=True)),
                ('order', models.SmallIntegerField(blank=True, null=True)),
                ('deleted', models.BooleanField(default=False, verbose_name='Borrado')),
                ('behavior', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='destinations', to='tool.behavior')),
            ],
            options={
                'verbose_name': 'Destino',
                'verbose_name_plural': 'Destinos',
                'ordering': ['order'],
            },
            bases=(models.Model, infrastructure.box.models.AssingMixin),
        ),
        migrations.CreateModel(
            name='Fragment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fragment_type', models.CharField(blank=True, choices=[('message', 'Mensaje'), ('behavior', 'Función Behavior'), ('embedded', 'Pieza embebida')], max_length=20, null=True)),
                ('order', models.SmallIntegerField(default=0)),
                ('addl_params', models.JSONField(blank=True, null=True)),
                ('deleted', models.BooleanField(default=False, verbose_name='Borrado')),
                ('file', models.FileField(blank=True, null=True, upload_to='box', verbose_name='Archivo o imagen')),
                ('media_url', models.CharField(blank=True, max_length=255, null=True, verbose_name='URL de multimedia')),
                ('media_type', models.CharField(blank=True, choices=[('image', 'Imagen'), ('video', 'Video'), ('audio', 'Audio'), ('file', 'Archivo'), ('sticker', 'Sticker')], max_length=20, null=True)),
                ('header', models.CharField(blank=True, max_length=255, null=True, verbose_name='Encabezado')),
                ('body', models.TextField(blank=True, null=True, verbose_name='Texto')),
                ('footer', models.CharField(blank=True, max_length=255, null=True, verbose_name='Pie de página')),
                ('reply_title', models.CharField(blank=True, max_length=80, null=True, verbose_name='Título de botón de respuesta')),
                ('behavior', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tool.behavior')),
            ],
            options={
                'verbose_name': 'Fragmento',
                'verbose_name_plural': 'Fragmentos',
                'ordering': ['order'],
            },
        ),
        migrations.CreateModel(
            name='Written',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('available', models.BooleanField(default=False, verbose_name='Disponible')),
                ('collection', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tool.collection')),
                ('extra', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='xtra.extra')),
            ],
            options={
                'verbose_name': 'Opción escrita',
                'verbose_name_plural': 'Opciones escritas',
            },
            bases=(models.Model, infrastructure.box.models.AssingMixin, infrastructure.box.models.DestinationMixin),
        ),
        migrations.CreateModel(
            name='Reply',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=255, null=True, verbose_name='text')),
                ('description', models.CharField(blank=True, max_length=255, null=True, verbose_name='Descripción')),
                ('large_title', models.CharField(blank=True, max_length=255, null=True, verbose_name='Título grande')),
                ('addl_params', models.JSONField(blank=True, null=True)),
                ('context', models.JSONField(blank=True, null=True, verbose_name='Contexto para chatGPT')),
                ('order', models.SmallIntegerField(blank=True, null=True)),
                ('is_jump', models.BooleanField(default=True, help_text='Funciona para evitar la pregunta')),
                ('use_piece_config', models.BooleanField(default=True)),
                ('deleted', models.BooleanField(default=False, verbose_name='Borrado')),
                ('destination', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='box.destination', verbose_name='Destino')),
                ('fragment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='box.fragment')),
            ],
            options={
                'verbose_name': 'Respuesta (Botón)',
                'verbose_name_plural': 'Respuestas (Botones)',
                'ordering': ['order'],
            },
            bases=(models.Model, infrastructure.box.models.AssingMixin, infrastructure.box.models.DestinationMixin),
        ),
        migrations.CreateModel(
            name='Piece',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, verbose_name='Nombre')),
                ('description', models.TextField(verbose_name='Descripción')),
                ('insistent', models.BooleanField(default=False, verbose_name='Insistente')),
                ('mandatory', models.BooleanField(default=False, verbose_name='Obligatorio')),
                ('config', models.JSONField(blank=True, default=dict, null=True)),
                ('order_in_crate', models.SmallIntegerField(blank=True, null=True)),
                ('deleted', models.BooleanField(default=False, verbose_name='Borrado')),
                ('behavior', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='tool.behavior')),
                ('crate', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pieces', to='flow.crate')),
                ('default_extra', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='xtra.extra')),
                ('written', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='box.written', verbose_name='Opción escrita')),
            ],
            options={
                'verbose_name': 'Pieza (Mensaje)',
                'verbose_name_plural': 'Piezas (Mensajes)',
                'ordering': ['order_in_crate'],
            },
            bases=(models.Model, infrastructure.box.models.AssingMixin, infrastructure.box.models.DestinationMixin),
        ),
        migrations.CreateModel(
            name='MessageLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link', models.URLField(blank=True, max_length=255, null=True)),
                ('message', models.CharField(blank=True, max_length=140, null=True)),
                ('qr_code_png', models.ImageField(blank=True, null=True, upload_to='qr_codes')),
                ('qr_code_svg', models.ImageField(blank=True, null=True, upload_to='qr_codes')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='place.account')),
            ],
            options={
                'verbose_name': 'Message Link',
                'verbose_name_plural': 'Message Links',
            },
            bases=(models.Model, infrastructure.box.models.DestinationMixin),
        ),
        migrations.AddField(
            model_name='fragment',
            name='embedded_piece',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='box.piece', verbose_name='Pieza embebida'),
        ),
        migrations.AddField(
            model_name='fragment',
            name='piece',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fragments', to='box.piece'),
        ),
        migrations.AddField(
            model_name='destination',
            name='message_link',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='destinations', to='box.messagelink', verbose_name='Link con mensaje'),
        ),
        migrations.AddField(
            model_name='destination',
            name='piece',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='destinations', to='box.piece'),
        ),
        migrations.AddField(
            model_name='destination',
            name='piece_dest',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='origins', to='box.piece'),
        ),
        migrations.AddField(
            model_name='destination',
            name='reply',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='destinations', to='box.reply'),
        ),
        migrations.AddField(
            model_name='destination',
            name='written',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='destinations', to='box.written', verbose_name='Opción escrita'),
        ),
    ]
