# Generated by Django 2.0.7 on 2018-10-10 05:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vpmotree', '0006_auto_20181009_1726'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='deliverable',
            options={'permissions': (('create_obj', 'Create Level Permissions'), ('delete_obj', 'Delete Level Permissions'), ('update_obj', 'Update Level Permissions'), ('read_obj', 'Read Level Permissions'), ('edit_role', 'Edit User Role Permissions'))},
        ),
    ]
