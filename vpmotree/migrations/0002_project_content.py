# Generated by Django 2.0.7 on 2018-09-27 05:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vpmotree', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='content',
            field=models.TextField(blank=True, null=True),
        ),
    ]
