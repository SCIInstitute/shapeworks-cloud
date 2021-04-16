import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient

from . import factories


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def authenticated_api_client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


register(factories.GroomedDatasetFactory)
register(factories.GroomedSegmentationFactory)
register(factories.OptimizationCheckpointFactory)
register(factories.OptimizationFactory)
register(factories.OptimizationParametersFactory)
register(factories.ProjectFactory)
register(factories.ShapeModelFactory)
