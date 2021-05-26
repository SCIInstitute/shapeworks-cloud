import pytest


@pytest.mark.django_db
def test_dataset(groomed_dataset):
    assert type(groomed_dataset.name) is str


# TODO real tests
