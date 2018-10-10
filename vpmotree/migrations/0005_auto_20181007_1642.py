# Generated by Django 2.0.7 on 2018-10-07 11:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vpmotree', '0004_auto_20181006_1807'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='project',
            options={'permissions': (('create_obj', 'Create Level Permissions'), ('delete_obj', 'Delete Level Permissions'), ('update_obj', 'Update Level Permissions'), ('read_obj', 'Read Level Permissions'), ('assign_contributor', 'Assign Contributor Permission'), ('assign_viewer', 'Assign Viewer Permission'), ('assign_admin', 'Assign Admin Permission'), ('edit_role', "Edit other user's role"))},
        ),
        migrations.AlterModelOptions(
            name='team',
            options={'permissions': (('create_obj', 'Create Level Permissions'), ('delete_obj', 'Delete Level Permissions'), ('update_obj', 'Update Level Permissions'), ('read_obj', 'Read Level Permissions'), ('add_user', 'Add User to Root'), ('remove_user', 'Remove User from Tree'), ('edit_role', "Edit other user's role"))},
        ),
    ]