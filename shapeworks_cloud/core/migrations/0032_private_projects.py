# Generated by Django 3.2.17 on 2023-04-27 08:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import s3_file_field.fields


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0031_Optional_Groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='creator',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name='project',
            name='name',
            field=models.CharField(default='My Project', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='private',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='dataset',
            name='thumbnail',
            field=s3_file_field.fields.S3FileField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='project',
            name='thumbnail',
            field=s3_file_field.fields.S3FileField(blank=True, null=True),
        ),
    ]
