# Generated by Django 3.2.23 on 2023-12-15 22:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0037_deepssm'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cacheddeepssm',
            name='data_loaders',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to='core.cacheddataloaders'
            ),
        ),
        migrations.AlterField(
            model_name='cacheddeepssm',
            name='model',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE, to='core.cachedmodel'
            ),
        ),
    ]
