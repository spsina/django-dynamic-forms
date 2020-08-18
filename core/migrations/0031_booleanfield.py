# Generated by Django 3.1 on 2020-08-17 18:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_auto_20200817_2216'),
    ]

    operations = [
        migrations.CreateModel(
            name='BooleanField',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('order', models.IntegerField(default=0)),
                ('value', models.BooleanField(blank=True, null=True)),
                ('answer_of', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='core.booleanfield')),
                ('field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='elements_booleanfield', to='core.field')),
                ('form', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='answers_booleanfield', to='core.form')),
            ],
            options={
                'abstract': False,
                'unique_together': {('answer_of', 'form')},
            },
        ),
    ]