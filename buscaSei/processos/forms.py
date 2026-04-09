from django import forms


class BuscaProcessoForm(forms.Form):
    """
    Formulário para busca de processo no SEI
    """
    numero_processo = forms.CharField(
        label='Número do Processo',
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 00000.000000/0000-00',
            'autocomplete': 'off'
        })
    )
    
    include_documentos = forms.BooleanField(
        label='Incluir documentos na busca',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
