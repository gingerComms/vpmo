# Generated by Django 2.0.7 on 2018-08-21 14:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vpmoapp', '0002_auto_20180820_1722'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliverable',
            name='parent_team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='vpmoapp.Deliverable'),
        ),
    ]
