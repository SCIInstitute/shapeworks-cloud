from .dataset import dataset_create, dataset_detail, dataset_edit, dataset_list
from .groomed import groomed_create, groomed_delete, groomed_detail, groomed_edit
from .home import home
from .particles import particles_create, particles_delete, particles_detail, particles_edit
from .segmentation import (
    segmentation_create,
    segmentation_delete,
    segmentation_detail,
    segmentation_edit,
)
from .shape_model import (
    shape_model_create,
    shape_model_delete,
    shape_model_detail,
    shape_model_edit,
)

__all__ = [
    'dataset_create',
    'dataset_detail',
    'dataset_edit',
    'dataset_list',
    'groomed_create',
    'groomed_detail',
    'groomed_edit',
    'groomed_delete',
    'home',
    'particles_create',
    'particles_detail',
    'particles_edit',
    'particles_delete',
    'segmentation_create',
    'segmentation_detail',
    'segmentation_edit',
    'segmentation_delete',
    'shape_model_create',
    'shape_model_detail',
    'shape_model_edit',
    'shape_model_delete',
]
