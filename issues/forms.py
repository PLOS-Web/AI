from django import forms

from issues.models import Category
from articleflow.models import Article


class IssueForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    description = forms.CharField(widget=forms.Textarea)
    article_pk = forms.ModelChoiceField(queryset=Article.objects.all(), widget=forms.HiddenInput())

    
