# Generated by Django 2.2.7 on 2020-06-03 09:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_auto_20200530_1316'),
    ]

    operations = [
        migrations.RenameField(
            model_name='indicator',
            old_name='configuration_json',
            new_name='configuration_format',
        ),
        migrations.AddField(
            model_name='alert',
            name='disabled',
            field=models.CharField(default=0, max_length=200),
        ),
        migrations.AlterField(
            model_name='alert',
            name='expiration',
            field=models.DateTimeField(default=None, null=True),
        ),
    ]
