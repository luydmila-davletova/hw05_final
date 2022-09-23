from django.core.paginator import Paginator

from .constants import AMOUNT_PUBLICATION


def get_page_context(request, posts):
    """Функция-паджинатор страниц."""
    paginator = Paginator(posts, AMOUNT_PUBLICATION)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return {
        'page_obj': page_obj,
    }

