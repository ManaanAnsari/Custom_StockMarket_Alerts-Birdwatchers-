# Generated by Django 3.0.5 on 2020-05-28 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_auto_20200527_1029'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='telegram_username',
            field=models.CharField(default=None, max_length=50, null=True),
        ),
    ]
