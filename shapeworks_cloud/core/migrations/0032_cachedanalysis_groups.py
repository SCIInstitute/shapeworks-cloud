# Generated by Django 3.2.18 on 2023-03-10 16:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0031_remove_cachedanalysis_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='cachedanalysis',
            name='groups',
            field=models.ManyToManyField(null=True, to='core.CachedAnalysisGroup'),
        ),
    ]
