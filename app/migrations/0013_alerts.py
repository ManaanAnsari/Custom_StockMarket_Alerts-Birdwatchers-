# Generated by Django 2.2.7 on 2020-06-14 10:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_indicator_log_created_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alerts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('conditions_json', models.TextField()),
                ('candle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.Candle')),
            ],
        ),
    ]