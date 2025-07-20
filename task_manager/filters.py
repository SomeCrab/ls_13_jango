import django_filters
from .models import Task

class TaskFilter(django_filters.FilterSet):
    deadline_wd = django_filters.NumberFilter(
        field_name='deadline',
        method='filter_by_weekday'
    )

    def filter_by_weekday(self, queryset, name, value):
        try:
            day_number = int(value)
            if day_number < 1 or day_number > 7:
                return queryset
        except (TypeError, ValueError):
            return queryset
        
        return queryset.filter(**{f'{name}__week_day': day_number})

    class Meta:
        model = Task
        fields = ['status']