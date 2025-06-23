# your_app/templatetags/pagination_tags.py

from django import template

register = template.Library()

@register.simple_tag
def render_pagination(page_obj, search_query=None):
    if not page_obj.paginator.num_pages > 1:
        return ''

    pagination_html = '<nav><ul class="pagination justify-content-center">'

    if page_obj.has_previous():
        pagination_html += f'<li class="page-item"><a class="page-link" href="?page={page_obj.previous_page_number()}'
        if search_query:
            pagination_html += f'&search={search_query}'
        pagination_html += '">Previous</a></li>'

    for page in range(1, page_obj.paginator.num_pages + 1):
        active = 'active' if page == page_obj.number else ''
        pagination_html += f'<li class="page-item {active}"><a class="page-link" href="?page={page}'
        if search_query:
            pagination_html += f'&search={search_query}'
        pagination_html += f'">{page}</a></li>'

    if page_obj.has_next():
        pagination_html += f'<li class="page-item"><a class="page-link" href="?page={page_obj.next_page_number()}'
        if search_query:
            pagination_html += f'&search={search_query}'
        pagination_html += '">Next</a></li>'

    pagination_html += '</ul></nav>'

    return pagination_html
