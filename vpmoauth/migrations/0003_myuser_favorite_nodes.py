# Generated by Django 2.0.7 on 2018-11-22 12:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vpmotree', '0012_auto_20181121_1523'),
        ('vpmoauth', '0002_auto_20181013_1538'),
    ]

    operations = [
        migrations.AddField(
            model_name='myuser',
            name='favorite_nodes',
            field=models.ManyToManyField(blank=True, to='vpmotree.TreeStructure'),
        ),
    ]