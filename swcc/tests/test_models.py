from pathlib import Path
from tempfile import TemporaryDirectory

from swcc import models

from . import factories


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
