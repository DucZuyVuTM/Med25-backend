from django import forms


class MessageForm(forms.Form):
    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Message content'
    )
