from django.views.generic import ListView

from errors.models import ErrorSet, Error
from articleflow.models import Article

class Errors(ListView):
    template_name = 'errors/error_list.html'

    def get_queryset(self):
        return ErrorSet.objects.filter(article__doi=self.kwargs['doi']).select_related('Errors')
    
    def get_context_data(self, **kwargs):
        article = Article.objects.get(doi=self.kwargs['doi'])
        context = ({
                'article': article,
                'errorset_list': self.get_queryset()
            })
        print context
        return context

    
