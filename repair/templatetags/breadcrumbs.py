from django import template
from django.urls import resolve, Resolver404

register = template.Library()

BREADCRUMB_LABELS = {
    'login_register': '🔑 Login',
    'home': '🏠 Home',
    'profile': '👤 Profile',
    'edit_profile': '✏️ Edit',
    'firmwares': '📁 Firmwares',
    'firmware_info': 'ℹ️ Info',
    'folder_detail': '📂 Folder',
    'add_repair': '➕ Add Repair',
    'edit_repair': '🛠️ Edit Repair',
    'generate_invoice': '🧾 Invoice',
    'add_customer': '➕ Customer',
    'account': '⚙️ Account',
    'add_staff': '👨‍🔧 Add Staff',
    'subscribe': '🔔 Subscribe',
    'grant_access': '🔓 Grant Access',
    'technician_dashboard': '👨‍🔧 Dashboard',
    'add_technician': '➕ Technician',
    'add_phone_model': '📱 Add Model',
    'get_device_models': '📱 Models',
    'delete_phone_model': '❌ Delete Model',
}

@register.simple_tag(takes_context=True)
def breadcrumb(context):
    request = context['request']
    path_parts = request.path.strip('/').split('/')
    url = ''
    crumbs = []

    for i, part in enumerate(path_parts):
        url += f'/{part}'

        try:
            # Try to resolve the URL only if it's not a parameter (e.g., '1')
            match = resolve(url)
            name = match.url_name
            label = BREADCRUMB_LABELS.get(name, part.replace('-', ' ').capitalize())
        except Resolver404:
            # Use the previous valid path segment if this is likely a dynamic part (like an ID)
            label = part if part.isdigit() else part.replace('-', ' ').capitalize()

        crumbs.append((label, url))

    return crumbs
