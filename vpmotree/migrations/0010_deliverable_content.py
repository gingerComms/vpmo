# Generated by Django 2.0.7 on 2018-11-11 01:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vpmotree', '0009_task'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliverable',
            name='content',
            field=models.TextField(blank=True, null=True),
        ),
    ]
