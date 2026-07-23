from django import forms
from .models import Glossary, GlossaryEntry


class GlossaryForm(forms.ModelForm):
    class Meta:
        model = Glossary
        fields = ['name', 'source_lang', 'target_lang', 'description', 'is_public']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'source_lang': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'en'}),
            'target_lang': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'hi'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }


class GlossaryEntryForm(forms.ModelForm):
    class Meta:
        model = GlossaryEntry
        fields = ['source', 'target', 'context', 'is_preferred']
        widgets = {
            'source': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Source term'}),
            'target': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Target translation'}),
            'context': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional context'}),
        }


class CSVImportForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-input', 'accept': '.csv'}))
