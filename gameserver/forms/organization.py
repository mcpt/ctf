from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class GroupJoinForm(forms.Form):
    access_code = forms.CharField(
        max_length=36,
        strip=True,
        widget=forms.TextInput(attrs={"placeholder": "Access Code"}),
        label="Enter the access code to join",
    )

    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop("group", None)
        super(GroupJoinForm, self).__init__(*args, **kwargs)

    def clean_access_code(self):
        if self.cleaned_data["access_code"] != self.group.access_code:
            raise ValidationError("Incorrect Access Code", code="forbidden")
