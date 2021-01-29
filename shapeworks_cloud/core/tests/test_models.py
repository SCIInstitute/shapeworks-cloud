import pytest


@pytest.mark.django_db
def test_dataset_num_segmentations(dataset, segmentation_factory):
    assert dataset.num_segmentations == 0
    segmentation_factory(dataset=dataset)
    assert dataset.num_segmentations == 1


@pytest.mark.django_db
def test_dataset_num_groomed(dataset, groomed_factory):
    assert dataset.num_groomed == 0
    groomed_factory(dataset=dataset)
    assert dataset.num_groomed == 1


@pytest.mark.django_db
def test_dataset_num_shape_models(dataset, shape_model_factory):
    assert dataset.num_shape_models == 0
    shape_model_factory(dataset=dataset)
    assert dataset.num_shape_models == 1


@pytest.mark.django_db
def test_shape_model_num_particles(shape_model, particles_factory):
    assert shape_model.num_particles == 0
    particles_factory(shape_model=shape_model)
    assert shape_model.num_particles == 1


@pytest.mark.django_db
def test_sizes(dataset, segmentation, groomed, shape_model, particles):
    assert segmentation.size == segmentation.blob.size
    assert groomed.size == groomed.blob.size
    assert particles.size == particles.blob.size
    assert shape_model.size == particles.size
    assert dataset.size == segmentation.size + groomed.size + particles.size
