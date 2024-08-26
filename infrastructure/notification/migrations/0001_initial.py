# Generated by Django 4.2.9 on 2024-08-20 04:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('place', '0003_account_app_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('limit_timing', models.IntegerField(blank=True, null=True)),
                ('unlimited_timing', models.BooleanField(default=False)),
                ('not_choisen_reconsidered_time', models.IntegerField(default=120, help_text='Minutes, for not chosen, not for failed')),
                ('account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='place.account')),
            ],
            options={
                'verbose_name': 'Notification Type',
                'verbose_name_plural': 'Notification Types',
                'unique_together': {('name', 'account')},
            },
        ),
        migrations.CreateModel(
            name='NotificationTiming',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timing', models.IntegerField(help_text='Minutes')),
                ('minimum_interest', models.IntegerField(default=0)),
                ('degradation_to_disinterest', models.IntegerField(default=0, help_text='0 - 100 %')),
                ('index', models.SmallIntegerField(default=0)),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timings', to='notification.notification')),
            ],
            options={
                'verbose_name': 'Notification Timing',
                'verbose_name_plural': 'Notification Timings',
            },
        ),
    ]
