from django.views.generic import ListView

from errors.models import ErrorSet, Error

class Errors(ListView):
    template_name = 'errors/error_list.html'

    #def get(self, request, *args, **kwargs):
    #    print args

    def get_queryset(self):
        doi = 'pone.0000001'
        return ErrorSet.objects.filter(article__doi=doi).select_related('Errors')

    
