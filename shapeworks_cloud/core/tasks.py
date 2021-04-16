# from io import BytesIO
# from pathlib import Path
# from tempfile import TemporaryDirectory
# from typing import List

# from celery import shared_task
# from django.core.files.base import ContentFile
# import numpy as np

# from . import models, serializers
# from .shapeworks_interface.convert import nrrd_to_vtp
# from .shapeworks_interface.optimize import optimize as _optimize


# @shared_task
# def optimize_shapes(optimization_id: int):
#     """Perform the optimization step for an initialized project."""
#     optimization: models.Optimization = models.Optimization.objects.get(pk=optimization_id)
#     project = optimization.project

#     optimization.running = True
#     optimization.save()

#     try:
#         parameters = serializers.OptimizationParametersSerializer(optimization.parameters).data
#         images: List[Path] = []
#         with TemporaryDirectory() as _dir:
#             dir = Path(_dir)
#             for image in project.groomed_dataset.segmentations.all().order_by('index'):
#                 # TODO: for very large images we would want to stream this to the filesystem
#                 data = image.blob.read()
#                 file_name = dir / image.name
#                 images.append(file_name)
#                 with file_name.open('wb') as f:
#                     f.write(data)

#             output = _optimize(images, parameters)
#             local = BytesIO()
#             world = BytesIO()

#             np.save(local, output.local)
#             np.save(world, output.world)

#             shape = models.ShapeModel()
#             shape.local.save('local.npy', ContentFile(local.getvalue()), save=False)
#             shape.world.save('world.npy', ContentFile(world.getvalue()), save=False)
#             shape.save()

#             optimization.shape_model = shape
#             optimization.save()

#     except Exception:
#         optimization.error = True
#         optimization.save()
#         raise
#     finally:
#         optimization.running = False
#         optimization.save()


# @shared_task
# def generate_groomed_segmentation_mesh(segmentation_id: int):
#     segmentation: models.GroomedSegmentation = models.GroomedSegmentation.objects.get(
#         pk=segmentation_id
#     )

#     vtp = nrrd_to_vtp(segmentation.blob.read())
#     segmentation.mesh.save(segmentation.blob.name + '.vtp', ContentFile(vtp), save=False)
#     segmentation.save(update_fields=['mesh'])


# @shared_task
# def generate_segmentation_mesh(segmentation_id: int):
#     segmentation: models.Segmentation = models.Segmentation.objects.get(pk=segmentation_id)

#     vtp = nrrd_to_vtp(segmentation.blob.read())
#     segmentation.mesh.save(segmentation.blob.name + '.vtp', ContentFile(vtp), save=False)
#     segmentation.save(update_fields=['mesh'])
