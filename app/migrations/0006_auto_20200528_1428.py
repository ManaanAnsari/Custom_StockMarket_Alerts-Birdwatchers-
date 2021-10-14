# Generated by Django 3.0.5 on 2020-05-28 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_userprofile_telegram_username'),
    ]

    operations = [
        migrations.RenameField(
            model_name='indicator',
            old_name='name',
            new_name='short_name',
        ),
        migrations.AddField(
            model_name='indicator',
            name='long_name',
            field=models.TextField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='instrument',
            name='display_name',
            field=models.TextField(default=None, null=True),
        ),
    ]