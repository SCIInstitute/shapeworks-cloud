from pathlib import Path

from setuptools import find_packages, setup

readme_file = Path(__file__).parent / 'README.md'
if readme_file.exists():
    with readme_file.open() as f:
        long_description = f.read()
else:
    # When this is first installed in development Docker, README.md is not available
    long_description = ''

setup(
    name='swcc',
    description='',
    version='1.0.0',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='Apache 2.0',
    author='Kitware, Inc.',
    author_email='kitware@kitware.com',
    keywords='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python',
    ],
    python_requires='>=3.8',
    packages=find_packages(exclude=['tests']),
    install_requires=[
        'click<9',  # celery depends on click<9, pin for now
        'click-pathlib',
        'django-s3-file-field-client',
        # if you override and install in python 3.7
        'importlib_metadata ; python_version < "3.8"',
        'openpyxl',
        'packaging',
        'pandas',
        'pydantic',
        'pyxdg',
        'requests',
        'requests-toolbelt',
        'rich',
        'toml',
        'tqdm',
        'typing-extensions ; python_version < "3.8"',
    ],
    entry_points={'console_scripts': ['swcc=swcc.cli:main']},
    extras_require={'dev': ['factory_boy', 'ipython', 'tox']},
)
