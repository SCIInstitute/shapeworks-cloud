# Generated by Django 3.2.18 on 2023-03-16 22:14

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0037_alter_cachedanalysisgroup_members'),
    ]

    operations = [
        migrations.RenameField(
            model_name='cachedanalysisgroup',
            old_name='members',
            new_name='groups',
        ),
    ]
