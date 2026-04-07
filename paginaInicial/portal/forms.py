from django import forms


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    token = forms.CharField(label="Token", widget=forms.PasswordInput)
