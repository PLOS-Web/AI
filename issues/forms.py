from django import forms
from django.forms import ModelForm
from django.contrib.comments.forms import CommentForm
from django.contrib.comments.models import Comment

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from crispy_forms.bootstrap import FormActions

from issues.models import Category, Issue, STATUS_CODES
from articleflow.models import Article



#class IssueForm(forms.Form):
#    category = forms.ModelChoiceField(queryset=Category.objects.all())
#    description = forms.CharField(widget=forms.Textarea)
#    article_pk = forms.ModelChoiceField(queryset=Article.objects.all(), widget=forms.HiddenInput())

class IssueForm(ModelForm):

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.form_class = 'tesssssst'
        self.helper.layout = Layout(
            Field('article'),
            Field('category', css_class='btn dropdown-toggle span2'),
            Field('description', rows="1", css_class='span5'),
            Submit('submit', 'Add Issue', css_class='btn-primary'),
            )
        
        super(IssueForm, self).__init__(*args, **kwargs)
        
    class Meta:
        model = Issue
        exclude = ('error','status','submitter', 'current_status')
        widgets = {
            'article' : forms.HiddenInput(),
            'description': forms.Textarea(),
            }
