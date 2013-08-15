from django import forms
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from crispy_forms.bootstrap import FormActions

class AssignmentForm(forms.Form):
    def __init__(self, u_ratios=None, state_pk=None, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)
        
        if u_ratios:
            for u_r in u_ratios:
                username = u_r['user'].username
                label = "%s (%s)" % (username, u_r['assignments'])
                if u_r['assignment_ratio']:
                    self.fields['user_%s' %username] = forms.IntegerField(initial=u_r['assignment_ratio'].weight, label=label)
                else:
                    self.fields['user_%s' %username] = forms.IntegerField(initial=0, label=label)

        if state_pk:
            self.fields['state'] = forms.IntegerField(widget=forms.HiddenInput(), initial=state_pk)

class ReportsDateRange(forms.Form):
    group_choices = ((1, 'PLOS Production'),(2, "Zyg"), (3, "Both"))
    typesetter_choices = ((1, 'CW QC'), (2, 'Merops QC'), (3, 'Merops+CW QC'), (4, 'Merops PM'))

    group = forms.ChoiceField(choices=group_choices)
    typesetter = forms.ChoiceField(choices=typesetter_choices)
    start_date = forms.DateTimeField(input_formats=['%m/%d/%Y'], widget=forms.DateInput(attrs={'class':'datepicker dateinput'}))
    end_date = forms.DateTimeField(input_formats=['%m/%d/%Y'], widget=forms.DateInput(attrs={'class':'datepicker dateinput'}))

class ReportsMeropsForm(forms.Form):
    typesetter_choices = ((1, 'CW'), (2, 'Merops'), (3, 'Both'))

    typesetter = forms.ChoiceField(choices=typesetter_choices)
    start_date = forms.DateTimeField(label="Start pubdate", input_formats=['%m/%d/%Y'], widget=forms.DateInput(attrs={'class':'datepicker dateinput'}))
    end_date = forms.DateTimeField(label="End pubdate", input_formats=['%m/%d/%Y'], widget=forms.DateInput(attrs={'class':'datepicker dateinput'}))

class AssignArticleForm(forms.Form):
    username = forms.ModelChoiceField(queryset=User.objects.filter(is_active=True).order_by('username'))
    article_pk = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, article, *args, **kwargs):
        super(AssignArticleForm, self).__init__(*args, **kwargs)
        self.article = article
        self.fields['article_pk'].initial = article.pk

    @property
    def helper(self):
        helper = FormHelper()
        action_url = reverse('assign_article', args=(self.article.doi,))
        helper.set_form_action(action_url)
        helper.layout = Layout(
            Field('username'),
            Field('article_pk'),
            Submit('submit', 'Assign')
            )
        return helper
   
class FileUpload(forms.Form):
    file = forms.FileField(label="Upload file", widget=forms.FileInput())

    def __init__(self, article, transition, *args, **kwargs):
        super(FileUpload, self).__init__(*args, **kwargs)
        self.article = article
        self.fields['article_pk'] = forms.IntegerField(widget=forms.HiddenInput(), initial=article.pk)
        self.transition = transition
        self.fields['requested_transition_pk'] = forms.IntegerField(widget=forms.HiddenInput(), initial=transition.pk)

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_class = 'form upload-form'
        #print "Helper: doi: %s" % reverse('detail_transition', args=(self.article.doi,))
        action_url = reverse('detail_transition_upload', args=(self.article.doi,))
        helper.set_form_action(action_url)
        helper.layout = Layout(
            Field('article_pk'),
            Field('requested_transition_pk'),
            Field('file'),
            Submit('submit', 'Submit', css_class='btn-primary'),
            )
        return helper


