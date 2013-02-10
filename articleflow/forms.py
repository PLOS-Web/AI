from django import forms

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



