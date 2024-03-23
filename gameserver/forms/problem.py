from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class FlagSubmissionForm(forms.Form):
    flag = forms.CharField(
        max_length=256,
        strip=True,
        label="",
        widget=forms.TextInput(attrs={"placeholder": "flag"}),
    )

    def __init__(self, *args, **kwargs):
        self.problem = kwargs.pop("problem", None)
        super(FlagSubmissionForm, self).__init__(*args, **kwargs)

        flag_format = self.problem.flag_format
        if flag_format is not None:
            self.fields["flag"].widget.attrs["placeholder"] = flag_format

    def clean_flag(self):
        if self.cleaned_data["flag"] != self.problem.flag:
            raise ValidationError("Incorrect Flag", code="incorrect")
