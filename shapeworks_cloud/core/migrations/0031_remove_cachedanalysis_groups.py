# Generated by Django 3.2.18 on 2023-03-10 16:21

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0030_cachedanalysisgroup_ratio'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cachedanalysis',
            name='groups',
        ),
    ]
