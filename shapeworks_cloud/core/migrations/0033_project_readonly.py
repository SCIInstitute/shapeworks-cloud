# Generated by Django 3.2.17 on 2023-06-01 15:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0032_private_projects'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='readonly',
            field=models.BooleanField(default=False),
        ),
    ]
