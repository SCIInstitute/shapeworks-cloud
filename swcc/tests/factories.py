from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

from factory import Factory, Faker, Sequence, SubFactory
from faker.providers import BaseProvider, file as file_provider, python as python_provider

from swcc import models


class FileUploadProvider(BaseProvider):
    _directory: Path

    def file(self, category=None, extension=None, null_chance=0):
        if self.generator.boolean(null_chance):
            return
        file_name = self.generator.file_name(extension=extension, category=category)
        file_path = self._directory / file_name
        with file_path.open('wb') as f:
            f.write(b' ')

        return file_path


Faker.add_provider(python_provider)
Faker.add_provider(file_provider)
Faker.add_provider(FileUploadProvider)


@contextmanager
def file_context():
    with TemporaryDirectory() as directory:
        p = Path(directory)
        FileUploadProvider._directory = p
        yield p

    del FileUploadProvider._directory


Faker.add_provider(FileUploadProvider)


class DatasetFactory(Factory):
    class Meta:
        model = models.Dataset

    name = Sequence(lambda n: f'dataset_{n}')
    license = Faker('sentence')
    description = Faker('sentence')
    acknowledgement = Faker('sentence')
    keywords = Faker('word')
    contributors = Faker('name')


class SubjectFactory(Factory):
    class Meta:
        model = models.Subject

    name = Sequence(lambda n: f'subject_{n}')
    dataset = SubFactory(DatasetFactory)


class SegmentationFactory(Factory):
    class Meta:
        model = models.Segmentation

    file = Faker('file', extension='nrrd')
    anatomy_type = Faker('word')
    subject = SubFactory(SubjectFactory)


class ProjectFactory(Factory):
    class Meta:
        model = models.Project

    file = Faker('file', extension='csv')
    keywords = Faker('word')
    description = Faker('sentence')
    dataset = SubFactory(DatasetFactory)


class GroomedSegmentationFactory(Factory):
    class Meta:
        model = models.GroomedSegmentation

    file = Faker('file', extension='nrrd')
    pre_cropping = Faker('file', extension='txt', null_chance=50)
    pre_alignment = Faker('file', extension='txt', null_chance=50)

    segmentation = SubFactory(SegmentationFactory)
    project = SubFactory(ProjectFactory)


class OptimizedShapeModelFactory(Factory):
    class Meta:
        model = models.OptimizedShapeModel

    project = SubFactory(ProjectFactory)
    parameters = Faker('pydict', value_types=[str, int, float])


class OptimizedParticlesFactory(Factory):
    class Meta:
        model = models.OptimizedParticles

    world = Faker('file', extension='txt')
    local = Faker('file', extension='txt')
    transform = Faker('file', extension='txt')
    shape_model = SubFactory(OptimizedShapeModelFactory)
    groomed_segmentation = SubFactory(GroomedSegmentationFactory)


class OptimizedPCAModelFactory(Factory):
    class Meta:
        model = models.OptimizedPCAModel

    mean_particles = Faker('file', extension='txt')
    pca_modes = Faker('file', extension='txt')
    eigen_spectrum = Faker('file', extension='txt')
    shape_model = SubFactory(OptimizedShapeModelFactory)
