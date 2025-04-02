from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone

from blogicum.settings import PAGINATE_BY
from .models import Post


def get_base_queryset(manager=Post.objects, filter=False, annotate=False):
    queryset = manager.select_related('author', 'location', 'category')
    if filter:
        queryset = queryset.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True,
        )
    if annotate:
        queryset = queryset.annotate(
            comment_count=Count('comments')).order_by('-pub_date')
    return queryset


def get_page(request, queryset):
    return Paginator(queryset, PAGINATE_BY).get_page(request.GET.get('page'))
