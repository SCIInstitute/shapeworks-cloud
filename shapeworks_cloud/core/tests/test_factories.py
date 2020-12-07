import pytest


@pytest.mark.django_db
def test_dataset(dataset):
    assert type(dataset.name) is str


# TODO real tests
