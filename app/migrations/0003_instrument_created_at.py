# Generated by Django 3.0.5 on 2020-05-20 11:13

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_instrument_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrument',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]