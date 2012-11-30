from django import forms
from django.forms import ModelForm

from issues.models import Category, Issue, STATUS_CODES
from articleflow.models import Article



#class IssueForm(forms.Form):
#    category = forms.ModelChoiceField(queryset=Category.objects.all())
#    description = forms.CharField(widget=forms.Textarea)
#    article_pk = forms.ModelChoiceField(queryset=Article.objects.all(), widget=forms.HiddenInput())

class IssueForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(IssueForm, self).__init__(*args, **kwargs)
        self.fields['category'].widget.attrs['class'] = 'btn dropdown-toggle'
        

    class Meta:
        model = Issue
        exclude = ('error','status','submitter', 'current_status')
        widgets = {
            'article' : forms.HiddenInput(),
            }
        
    
