# Generated by Django 3.1 on 2020-08-19 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0036_auto_20200819_1645'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checkboxelement',
            name='values',
            field=models.ManyToManyField(blank=True, to='core.CharField'),
        ),
    ]
