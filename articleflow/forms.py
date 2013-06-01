from django import forms
from django.core.urlresolvers import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from crispy_forms.bootstrap import FormActions

class AssignmentForm(forms.Form):
    def __init__(self, u_ratios=None, state_pk=None, *args, **kwargs):
        super(AssignmentForm, self).__init__(*args, **kwargs)
        
        if u_ratios:
            for u_r in u_ratios:
                username = u_r['user'].username
                if u_r['assignment_ratio']:
                    self.fields['user_%s' %username] = forms.IntegerField(initial=u_r['assignment_ratio'].weight, label=username)
                else:
                    self.fields['user_%s' %username] = forms.IntegerField(initial=0, label=username)

        if state_pk:
            self.fields['state'] = forms.IntegerField(widget=forms.HiddenInput(), initial=state_pk)

class ReportsDateRange(forms.Form):
    group_choices = ((1, 'Production'),(2, "Zyg"), (3, "Both"))

    group = forms.ChoiceField(choices=group_choices)
    start_date = forms.DateTimeField(input_formats=['%m/%d/%Y'], widget=forms.DateInput(attrs={'class':'datepicker dateinput'}))
    end_date = forms.DateTimeField(input_formats=['%m/%d/%Y'], widget=forms.DateInput(attrs={'class':'datepicker dateinput'}))
 
   
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
        action_url = reverse('detail_transition', args=(self.article.doi,))
        helper.set_form_action(action_url)
        helper.layout = Layout(
            Field('article_pk'),
            Field('transition_pk'),
            Field('file'),
            Submit('submit', 'Submit', css_class='btn-primary'),
            )
        return helper


