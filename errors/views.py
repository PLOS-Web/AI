from django.views.generic import ListView

from errors.models import ErrorSet, Error

class Errors(ListView):
    template_name = 'errors/error_list.html'

    def get_queryset(self):
        return ErrorSet.objects.filter(article__doi=self.kwargs['doi']).select_related('Errors')

    
