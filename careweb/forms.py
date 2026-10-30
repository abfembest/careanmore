import re

from django import forms

from .models import Enquiry, Service
from .security import BotProtectionMixin


class EnquiryForm(BotProtectionMixin, forms.ModelForm):
    consent = forms.BooleanField(
        required=True,
        label='I have read the privacy information and understand this is an enquiry, not a care booking.',
        error_messages={'required': 'Confirm you have read the privacy information to send your enquiry.'},
    )

    class Meta:
        model = Enquiry
        fields = ['name', 'contact_method', 'email', 'phone', 'postcode', 'topic', 'service', 'message', 'consent']
        widgets = {
            'name': forms.TextInput(attrs={'autocomplete': 'name'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email'}),
            'phone': forms.TextInput(attrs={'autocomplete': 'tel', 'type': 'tel', 'inputmode': 'tel'}),
            'postcode': forms.TextInput(attrs={'autocomplete': 'postal-code', 'class': 'input-short'}),
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'How can we help?'}),
        }
        labels = {
            'message': 'Short message (please avoid sensitive medical details)',
            'postcode': 'Postcode (optional)',
        }
        help_texts = {
            'postcode': 'Helps us check whether we cover your area.',
        }
        error_messages = {
            'name': {'required': 'Enter your name.'},
            'contact_method': {'required': 'Choose how you would like us to contact you.'},
            'topic': {'required': 'Choose what you would like to discuss.'},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].queryset = Service.objects.published()
        self.fields['service'].required = False
        self.fields['service'].empty_label = 'Not sure yet'
        self.fields['contact_method'].choices = [('', 'Choose one')] + Enquiry.CONTACT_METHODS
        self.fields['topic'].choices = [('', 'Choose a topic')] + Enquiry.TOPICS
        for name in ('name', 'contact_method', 'topic'):
            self.fields[name].required = True

    MAX_LINKS = 2

    def clean_message(self):
        message = self.cleaned_data.get('message', '')
        if len(re.findall(r'https?://|www\.', message, re.I)) > self.MAX_LINKS:
            raise forms.ValidationError('Remove the web links from your message and try again.')
        return message

    def clean(self):
        data = super().clean()
        method = data.get('contact_method')
        if method == 'email' and not data.get('email'):
            self.add_error('email', 'Enter an email address so we can reply by email.')
        if method == 'phone' and not data.get('phone'):
            self.add_error('phone', 'Enter a phone number so we can call you back.')
        return data
