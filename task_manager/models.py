from django.db import models
from django.contrib.postgres.indexes import BrinIndex
from .managers import CategorySoftDeleteManager
from django.utils import timezone
from django.conf import settings

# CONSTANTS
STATUS_CHOICES = {
    'NEW': 'New',
    'IN_PROGRESS': 'In progress',
    'PENDING': 'Pending',
    'BLOCKED': 'Blocked',
    'DONE': 'Done'
}


# MODELS
class Category(models.Model):
    ''' Task category model. '''
    name = models.CharField(max_length=30, verbose_name="Category Title", unique=True)
    is_deleted = models.BooleanField(verbose_name="Is Deleted", default=False)
    deleted_at = models.DateTimeField(verbose_name="Deleted At", null=True, default=None)
    objects = CategorySoftDeleteManager()
    all_objects = models.Manager()

    def delete(self):
        """ Soft delete. """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """ Restore a soft-deleted. """
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def hard_delete(self):
        """ Hard delete. """
        super().delete()

    def __str__(self):
        return f'{self.name}'
    
    def __repr__(self):
        return f'id: {self.id}, name: {self.name}'

    class Meta:
        db_table = 'task_manager_category'
        verbose_name = 'Category'
        verbose_name_plural = "Categories"
        permissions = [
            ("can_get_statistic", "Can get genres statistic"),
            ]


class Task(models.Model):
    ''' Main task model. '''
    title = models.CharField(max_length=100, verbose_name="Task Title", blank=False)
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    category = models.ManyToManyField(Category, related_name='tasks', verbose_name="Task Categories")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name='tasks'
    )
    status = models.CharField(
        max_length=15,
        blank=False,
        choices=STATUS_CHOICES,
        default='NEW',
        verbose_name="Status"
    )
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Deadline")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.title} #{self.id} ({self.get_status_display()})"
    
    class Meta:
        db_table = 'task_manager_task'
        ordering = ['-created_at']
        verbose_name = 'Task'
        indexes = [BrinIndex(fields=['created_at'], name='task_created_at_brin')]


class SubTask(models.Model):
    ''' Subtask model. '''
    title = models.CharField(max_length=100, verbose_name="Subtask Title", blank=False)
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='subtasks'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        related_name='subtasks'
    )
    status = models.CharField(
        max_length=15,
        blank=False,
        choices=STATUS_CHOICES,
        default='NEW',
        verbose_name="Status"
    )
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="Deadline")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    def __str__(self):
        return f"{self.title} ({self.get_status_display()}) [Subtask of {self.task.title} #{self.task.id}]"
    
    class Meta:
        db_table = 'task_manager_subtask'
        ordering = ['-created_at']
        verbose_name = 'SubTask'
        indexes = [BrinIndex(fields=['created_at'], name='subtask_created_at_brin')]