from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import CachedAnalysis, CachedAnalysisMode, CachedAnalysisModePCA, Project


@receiver(pre_delete, sender=Project)
def delete_cached_analysis(sender, instance, using, **kwargs):
    CachedAnalysisModePCA.objects.filter(
        cachedanalysismode__cachedanalysis__project=instance
    ).delete()
    CachedAnalysisMode.objects.filter(cachedanalysis__project=instance).delete()
    CachedAnalysis.objects.filter(project=instance).delete()
