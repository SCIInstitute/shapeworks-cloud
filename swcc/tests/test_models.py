from pathlib import Path
from tempfile import TemporaryDirectory

from factory import Factory
import pytest
import requests

from swcc import models

from . import factories

_factories = [
    f
    for f in factories.__dict__.values()
    if isinstance(f, type) and issubclass(f, Factory) and f is not Factory
]


def test_api_common(session):
    dataset1 = factories.DatasetFactory().create()
    dataset2 = factories.DatasetFactory().create()

    other = models.Dataset.from_id(dataset1.id)
    assert other.name == dataset1.name

    assert {d.id for d in models.Dataset.list()} == {dataset1.id, dataset2.id}

    dataset1.delete()
    assert {d.id for d in models.Dataset.list()} == {dataset2.id}


def test_file_download_api(session):
    with TemporaryDirectory() as d:
        directory = Path(d)
        file = directory / 'test_file.nrrd'
        with file.open('w') as f:
            f.write('file content')
        segmentation = factories.SegmentationFactory(file=file).create()
        segmentation = models.Segmentation.from_id(segmentation.id)

        assert file.name in segmentation.file.url

        d1 = directory / '1'
        d1.mkdir()
        segmentation.file.download(d1)

        download_file = d1 / 'test_file.nrrd'
        assert download_file.exists()
        with download_file.open('r') as f:
            assert f.read() == 'file content'

        d2 = directory / '2'
        d2.mkdir()
        files = list(segmentation.download_files(d2))
        assert files == [d2 / 'test_file.nrrd']


@pytest.mark.parametrize('factory', _factories)
def test_model_crud(session, factory):
    obj = factory().create()
    model = obj.__class__

    assert model.from_id(obj.id).id == obj.id
    assert obj.id in {o.id for o in model.list()}

    obj.delete()
    assert obj.id not in {o.id for o in model.list()}


def test_get_dataset_by_name(session):
    factories.DatasetFactory(name='dataset1').create()
    factories.DatasetFactory(name='dataset2').create()

    dataset = models.Dataset.from_name('dataset1')
    assert dataset and dataset.name == 'dataset1'

    dataset = models.Dataset.from_name('dataset2')
    assert dataset and dataset.name == 'dataset2'

    dataset = models.Dataset.from_name('dataset3')
    assert dataset is None


def test_dataset_force_create_overwrite(session):
    old_dataset = factories.DatasetFactory(name='dataset1').create()
    assert models.Dataset.from_id(old_dataset.id)

    new_dataset = models.Dataset(
        name='dataset1',
        license=old_dataset.license,
        description=old_dataset.description,
        acknowledgement=old_dataset.acknowledgement,
    ).force_create()
    new_dataset.assert_remote()

    # The new dataset should now exist on the server
    assert models.Dataset.from_name('dataset1') == new_dataset
    # The old dataset should no longer exist on the server
    with pytest.raises(requests.exceptions.HTTPError):
        # Gotta clear the cache first
        session.cache[models.Dataset] = {}
        old = models.Dataset.from_id(old_dataset.id)
        assert old


def test_dataset_force_create_no_existing(session):
    dataset = models.Dataset(
        name='dataset1',
        license='license',
        description='description',
        acknowledgement='acknowledgement',
    ).force_create()
    dataset.assert_remote()

    assert models.Dataset.from_name('dataset1') == dataset


@pytest.mark.parametrize(
    'version',
    [0, 1, 9, 10, 99],
)
def test_dataset_force_create_backup(session, version):
    old_name = f'dataset-v{version}'
    new_name = f'dataset-v{version+1}'
    old_dataset = factories.DatasetFactory(name=old_name).create()
    assert models.Dataset.from_id(old_dataset.id)

    new_dataset = models.Dataset(
        name=old_name,
        license=old_dataset.license,
        description=old_dataset.description,
        acknowledgement=old_dataset.acknowledgement,
    ).force_create(backup=True)
    new_dataset.assert_remote()

    # The old dataset should still exist on the server
    assert models.Dataset.from_name(old_name) == old_dataset
    # The new dataset should also exist on the server
    assert models.Dataset.from_name(new_name) == new_dataset
    # The new dataset should have its name changed in place
    assert new_dataset.name == new_name


def test_dataset_force_create_backup_no_version_suffix(session):
    old_dataset = factories.DatasetFactory(name='dataset1').create()
    assert models.Dataset.from_id(old_dataset.id)

    new_dataset = models.Dataset(
        name='dataset1',
        license=old_dataset.license,
        description=old_dataset.description,
        acknowledgement=old_dataset.acknowledgement,
    ).force_create(backup=True)
    new_dataset.assert_remote()

    # The old dataset should still exist on the server
    assert models.Dataset.from_name('dataset1') == old_dataset
    # The new dataset should also exist on the server
    assert models.Dataset.from_name('dataset1-v1') == new_dataset


def test_dataset_force_create_backup_multiple_conflicts(session):
    old_dataset = factories.DatasetFactory(name='dataset').create()
    factories.DatasetFactory(name='dataset-v1').create()
    factories.DatasetFactory(name='dataset-v2').create()
    factories.DatasetFactory(name='dataset-v3').create()
    assert models.Dataset.from_id(old_dataset.id)

    new_dataset = models.Dataset(
        name='dataset',
        license=old_dataset.license,
        description=old_dataset.description,
        acknowledgement=old_dataset.acknowledgement,
    ).force_create(backup=True)
    new_dataset.assert_remote()

    # The new dataset should cascade up until it reaches dataset-v4
    assert models.Dataset.from_name('dataset-v4') == new_dataset
