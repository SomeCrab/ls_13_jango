from django.db import models
from django.contrib.postgres.indexes import BrinIndex

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

    def __str__(self):
        return f'{self.name}'
    
    def __repr__(self):
        return f'id: {self.id}, name: {self.name}'

    class Meta:
        db_table = 'task_manager_category'
        verbose_name = 'Category'
        verbose_name_plural = "Categories"


class Task(models.Model):
    ''' Main task model. '''
    title = models.CharField(max_length=100, verbose_name="Task Title", unique_for_date='created_at', blank=False)
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    category = models.ManyToManyField(Category, related_name='tasks', verbose_name="Task Categories")
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
    title = models.CharField(max_length=100, verbose_name="Subtask Title", unique_for_date='created_at', blank=False)
    description = models.TextField(null=True, blank=True, verbose_name="Description")
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
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