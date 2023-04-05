from django.conf import settings
from django.core.paginator import Paginator


def paginating(request, data):
    paginator = Paginator(data, settings.POSTS_NUM)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
