# Generated by Django 2.2.7 on 2020-06-23 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_notification_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='indicator',
            name='class_input_variables',
            field=models.TextField(default=None, null=True),
        ),
    ]
