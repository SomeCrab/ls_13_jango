from django.db import models

class CategorySoftDeleteManager(models.Manager):
    """ Exclude soft-deleted objects by default. """
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def include_deleted(self):
        """ Include soft-deleted objects. """
        return super().get_queryset()

    def only_deleted(self):
        """ Only soft-deleted objects. """
        return super().get_queryset().filter(is_deleted=True)