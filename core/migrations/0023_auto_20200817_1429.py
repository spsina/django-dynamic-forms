# Generated by Django 3.1 on 2020-08-17 09:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_auto_20200817_1428'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='template',
            name='base_template',
        ),
        migrations.RemoveField(
            model_name='template',
            name='filler',
        ),
    ]
