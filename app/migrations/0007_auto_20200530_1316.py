# Generated by Django 3.0.5 on 2020-05-30 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_auto_20200528_1428'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indicator',
            name='code',
            field=models.TextField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='indicator',
            name='configuration_json',
            field=models.TextField(default=None, null=True),
        ),
    ]
