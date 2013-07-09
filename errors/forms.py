from django.core.urlresolvers import reverse

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from crispy_forms.bootstrap import FormActions

def errorsetlist_form_helper(errorset):
    helper = FormHelper()
    action_url = reverse('errorsetlist', args=(errorset.pk,))
    helper.set_form_action(action_url)
    helper.form_class = 'form-inline error-filter-form'
    helper.form_method = 'GET'
    helper.form_id = 'errorset-filter-form-%s' % errorset.pk
    helper.layout = Layout(
        'level',
        Submit('filter', 'Filter')
        )
    return helper
