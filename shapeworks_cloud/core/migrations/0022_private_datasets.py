# Generated by Django 3.2.16 on 2023-01-20 23:03

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0021_mean_particles'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dataset',
            name='file',
        ),
        migrations.AddField(
            model_name='dataset',
            name='creator',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='dataset',
            name='private',
            field=models.BooleanField(default=False),
        ),
    ]