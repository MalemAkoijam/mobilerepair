# repair/context_processors.py

from .forms import SubscribeForm

def subscribe_form(request):
    return {
        'form': SubscribeForm()
    }