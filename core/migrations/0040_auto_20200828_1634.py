# Generated by Django 3.1 on 2020-08-28 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0039_auto_20200822_0701'),
    ]

    operations = [
        migrations.AddField(
            model_name='template',
            name='access_level',
            field=models.PositiveBigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='access_level',
            field=models.PositiveBigIntegerField(default=0),
        ),
    ]
