from pathlib import Path

from setuptools import find_packages, setup

readme_file = Path(__file__).parent / 'README.md'
if readme_file.exists():
    with readme_file.open() as f:
        long_description = f.read()
else:
    # When this is first installed in development Docker, README.md is not available
    long_description = """
        This is a cloud based webapp alternative to a
        desktop application called ShapeWorks Studio,
        made in collaboration with ShapeWorks.
        See the [ShapeWorks Website](http://sciinstitute.github.io/ShapeWorks/)
        for more details.
    """

setup(
    name='shapeworks-cloud',
    version='1.0',  # Applies to all patches to the current minor version
    description='A webapp alternative to ShapeWorks Studio, made in collaboration with ShapeWorks',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache 2.0',
    author='Kitware, Inc.',
    author_email='kitware@kitware.com',
    keywords='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django :: 3.0',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python',
    ],
    python_requires='>=3.8',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'celery',
        'django',
        'django-admin-display',
        'django-allauth',
        'django-configurations[database,email]',
        'django-extensions',
        'django-filter',
        'django-oauth-toolkit',
        'djangorestframework',
        'drf-extensions>=0.7.0',
        'drf-yasg',
        'pandas',
        'pyrabbit',
        'ngpuinfo',
        'swcc',
        # Production-only
        'django-composed-configuration[prod]',
        'django-s3-file-field[boto3]<1',  # v1 has breaking changes
        'gunicorn',
        'numpy',
    ],
    extras_require={
        'dev': [
            'django-composed-configuration[dev]',
            'django-debug-toolbar',
            'django-s3-file-field[minio]<1',
            'ipython',
            'openpyxl',
            'tox',
        ]
    },
)
