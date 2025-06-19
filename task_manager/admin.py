from django.contrib import admin
from task_manager.models import (
    Category,
    Task,
    SubTask,
)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_at', 'deadline',)
    search_fields = ('title',)
    list_filter = ('deadline', 'status', 'category',)
    fields = ('title', 'description', 'category', 'status', 'deadline',)
    list_per_page = 10


@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'created_at', 'deadline',)
    search_fields = ('title', 'task',)
    list_filter = ('deadline', 'status', 'task',)
    fields = ('title', 'description', 'task', 'status', 'deadline',)
    list_per_page = 10


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    fields = ('name',)
    list_per_page = 10