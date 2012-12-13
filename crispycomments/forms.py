from django import forms
from django.contrib.comments.forms import CommentForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit
from crispy_forms.bootstrap import FormActions

from articleflow.models import Article
from issues.models import Issue


class IssueCommentForm(CommentForm):
    def __init__(self, *args, **kwargs):
        print args
        submit_label = 'Add thing'

        if isinstance(args[0], Article):
            submit_label = 'Add note'
        elif isinstance(args[0], Issue):
            submit_label = 'Add comment'
        
        print submit_label
        #import pdb; pdb.set_trace()
        print isinstance(args[0], Issue)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('comment', rows=2),
            Submit('submit', submit_label, css_class='btn-primary'),
            )
        super(CommentForm, self).__init__(*args, **kwargs)
        
