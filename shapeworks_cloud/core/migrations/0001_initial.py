# Generated by Django 3.2 on 2021-05-19 04:02

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import s3_file_field.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = []  # type: ignore

    operations = [
        migrations.CreateModel(
            name='Dataset',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'created',
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name='created'
                    ),
                ),
                (
                    'modified',
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name='modified'
                    ),
                ),
                ('name', models.CharField(max_length=255, unique=True)),
                ('license', models.TextField()),
                ('description', models.TextField()),
                ('acknowledgement', models.TextField()),
                ('keywords', models.CharField(default='', max_length=255)),
                ('contributors', models.TextField(default='')),
                ('publications', models.TextField(default='')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OptimizedParticles',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('world', s3_file_field.fields.S3FileField()),
                ('local', s3_file_field.fields.S3FileField()),
                ('transform', s3_file_field.fields.S3FileField()),
            ],
        ),
        migrations.CreateModel(
            name='OptimizedShapeModel',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('parameters', models.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'created',
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name='created'
                    ),
                ),
                (
                    'modified',
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name='modified'
                    ),
                ),
                ('file', s3_file_field.fields.S3FileField()),
                ('keywords', models.CharField(default='', max_length=255)),
                ('description', models.TextField(default='')),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Segmentation',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('file', s3_file_field.fields.S3FileField()),
                ('anatomy_type', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='GroomedSegmentation',
            fields=[
                ('file', s3_file_field.fields.S3FileField()),
                ('pre_cropping', s3_file_field.fields.S3FileField(null=True)),
                ('pre_alignment', s3_file_field.fields.S3FileField(null=True)),
                (
                    'segmentation',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name='groomed',
                        serialize=False,
                        to='core.segmentation',
                    ),
                ),
                (
                    'project',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='groomed_segmentations',
                        to='core.project',
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='OptimizedPCAModel',
            fields=[
                (
                    'shape_model',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name='pca_model',
                        serialize=False,
                        to='core.optimizedshapemodel',
                    ),
                ),
                ('mean_particles', s3_file_field.fields.S3FileField()),
                ('pca_modes', s3_file_field.fields.S3FileField()),
                ('eigen_spectrum', s3_file_field.fields.S3FileField()),
            ],
        ),
        migrations.CreateModel(
            name='OptimizedSurfaceReconstruction',
            fields=[
                (
                    'particles',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        related_name='surface_reconstruction',
                        serialize=False,
                        to='core.optimizedparticles',
                    ),
                ),
                ('sample_reconstruction', s3_file_field.fields.S3FileField()),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'created',
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name='created'
                    ),
                ),
                (
                    'modified',
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name='modified'
                    ),
                ),
                ('name', models.CharField(max_length=255, unique=True)),
                (
                    'dataset',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='subjects',
                        to='core.dataset',
                    ),
                ),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='segmentation',
            name='subject',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='segmentations',
                to='core.subject',
            ),
        ),
        migrations.CreateModel(
            name='OptimizedSurfaceReconstructionMeta',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('method', models.CharField(max_length=255)),
                ('reconstruction_params', s3_file_field.fields.S3FileField()),
                ('template_reconstruction', s3_file_field.fields.S3FileField()),
                (
                    'shape_model',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='core.optimizedshapemodel',
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name='optimizedshapemodel',
            name='project',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='optimized_shape_models',
                to='core.project',
            ),
        ),
        migrations.AddField(
            model_name='optimizedparticles',
            name='shape_model',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='particles',
                to='core.optimizedshapemodel',
            ),
        ),
        migrations.AddField(
            model_name='optimizedparticles',
            name='groomed_segmentation',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='+',
                to='core.groomedsegmentation',
            ),
        ),
    ]