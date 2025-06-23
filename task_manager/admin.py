from django.contrib import admin
from task_manager.models import (
    Category,
    Task,
    SubTask,
)


class SubTaskInline(admin.TabularInline):
    model = SubTask
    extra = 1
    fields = ('title', 'description', 'status', 'deadline',)
    show_change_link = True


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('short_title', 'short_desc', 'status', 'created_at', 'deadline',)
    search_fields = ('title',)
    list_filter = ('deadline', 'status', 'category',)
    fields = ('title', 'description', 'category', 'status', 'deadline',)
    list_per_page = 10
    inlines = [SubTaskInline]
    actions = ['mark_as_done', 'mark_as_in_progress']

    def short_desc(self, obj):
        return obj.description[:40] + ('...' if len(obj.description) > 40 else '')
    short_desc.short_description = 'description'

    def short_title(self, obj):
        return obj.title[:10] + ('...' if len(obj.title) > 10 else '')
    short_title.short_description = 'Title'

    @admin.action(description="Mark as Done")
    def mark_as_done(self, request, queryset):
        updated = queryset.update(status='DONE')
        self.message_user(request, f"Marked {updated} item's as Done.")

    @admin.action(description="Mark as In Progress")
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='IN_PROGRESS')
        self.message_user(request, f"Marked {updated} item's as In Progress.")

@admin.register(SubTask)
class SubTaskAdmin(admin.ModelAdmin):
    list_display = ('title','status', 'task', 'created_at', 'deadline',)
    search_fields = ('title', 'task',)
    list_filter = ('deadline', 'status', 'task',)
    fields = ('title', 'description', 'task', 'status', 'deadline',)
    list_per_page = 10

    actions = ['mark_as_done', 'mark_as_in_progress']

    @admin.action(description="Mark as Done")
    def mark_as_done(self, request, queryset):
        updated = queryset.update(status='DONE')
        self.message_user(request, f"Marked {updated} item's as Done.")

    @admin.action(description="Mark as In Progress")
    def mark_as_in_progress(self, request, queryset):
        updated = queryset.update(status='IN_PROGRESS')
        self.message_user(request, f"Marked {updated} item's as In Progress.")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    fields = ('name',)
    list_per_page = 10