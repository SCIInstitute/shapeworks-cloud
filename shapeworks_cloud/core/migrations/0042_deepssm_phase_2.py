# Generated by Django 3.2.24 on 2024-02-13 21:15

from django.db import migrations, models
import django.db.models.deletion
import s3_file_field.fields


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0041_get_contents_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='CachedDeepSSMAug',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visualization', s3_file_field.fields.S3FileField()),
            ],
        ),
        migrations.CreateModel(
            name='CachedDeepSSMAugPair',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mesh', s3_file_field.fields.S3FileField()),
                ('particles', s3_file_field.fields.S3FileField()),
            ],
        ),
        migrations.CreateModel(
            name='CachedDeepSSMTesting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='CachedDeepSSMTestingData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mean_distance', models.FloatField()),
                ('mesh', s3_file_field.fields.S3FileField()),
                ('particles', s3_file_field.fields.S3FileField()),
            ],
        ),
        migrations.RenameModel(
            old_name='CachedAugmentationPair',
            new_name='CachedDeepSSMTraining',
        ),
        migrations.RemoveField(
            model_name='cachedaugmentation',
            name='pairs',
        ),
        migrations.RemoveField(
            model_name='cachedmodel',
            name='examples',
        ),
        migrations.RemoveField(
            model_name='cachedmodel',
            name='ft_predictions',
        ),
        migrations.RemoveField(
            model_name='cachedmodel',
            name='pca_predictions',
        ),
        migrations.RemoveField(
            model_name='cachedmodelexamples',
            name='best',
        ),
        migrations.RemoveField(
            model_name='cachedmodelexamples',
            name='median',
        ),
        migrations.RemoveField(
            model_name='cachedmodelexamples',
            name='worst',
        ),
        migrations.RenameField(
            model_name='cacheddeepssmtraining',
            old_name='file',
            new_name='data_table',
        ),
        migrations.RenameField(
            model_name='cacheddeepssmtraining',
            old_name='particles',
            new_name='visualization',
        ),
        migrations.RemoveField(
            model_name='cacheddeepssm',
            name='data_loaders',
        ),
        migrations.RemoveField(
            model_name='cacheddeepssm',
            name='model',
        ),
        migrations.AddField(
            model_name='cacheddeepssm',
            name='training',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.cacheddeepssmtraining'),
        ),
        migrations.DeleteModel(
            name='CachedDataLoaders',
        ),
        migrations.DeleteModel(
            name='CachedExample',
        ),
        migrations.DeleteModel(
            name='CachedModel',
        ),
        migrations.DeleteModel(
            name='CachedModelExamples',
        ),
        migrations.DeleteModel(
            name='CachedPrediction',
        ),
        migrations.DeleteModel(
            name='CachedTensors',
        ),
        migrations.AddField(
            model_name='cacheddeepssmtesting',
            name='data',
            field=models.ManyToManyField(to='core.CachedDeepSSMTestingData'),
        ),
        migrations.AddField(
            model_name='cacheddeepssmaug',
            name='pairs',
            field=models.ManyToManyField(to='core.CachedDeepSSMAugPair'),
        ),
        migrations.AddField(
            model_name='cacheddeepssm',
            name='testing',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.cacheddeepssmtesting'),
        ),
        migrations.AlterField(
            model_name='cacheddeepssm',
            name='augmentation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.cacheddeepssmaug'),
        ),
        migrations.DeleteModel(
            name='CachedAugmentation',
        ),
    ]
