import inspect

from django.contrib import admin
import django.db.models

from . import models as models

for key in dir(models):
    prop = getattr(models, key, None)
    if hasattr(prop, '_meta') and not getattr(prop._meta, 'abstract', None):
        if inspect.isclass(prop) and issubclass(prop, django.db.models.Model):
            admin.site.register(getattr(models, key))
