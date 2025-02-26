from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, TYPE_CHOICES, ZODIAC_CHOICES, GENDER_CHOICES

# Widgets

class SelectWithDisabledFirstOption(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        if index == 0:  # Disable the first option
            option['attrs']['disabled'] = True
        return option
    
# Forms

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class ProfileForm(forms.ModelForm):
    # Add "Sélectionner" as the first option with a data-placeholder attribute
    gender = forms.ChoiceField(
        choices=[("", "Sélectionner")] + list(GENDER_CHOICES),
        widget=forms.Select(attrs={"data-placeholder": "true"}),
    )
    zodiac_sign = forms.ChoiceField(
        choices=[("", "Sélectionner")] + list(ZODIAC_CHOICES),
        widget=forms.Select(attrs={"data-placeholder": "true"}),
        required=False,
    )
    type = forms.ChoiceField(
        choices=[("", "Sélectionner")] + list(TYPE_CHOICES),
        widget=forms.Select(attrs={"data-placeholder": "true"}),
        required=False,
    )

    class Meta:
        model = Profile
        fields = [
            'birthdate', 'type', 'zodiac_sign', 'gender',
            'desc', 'localisation', 'loisirs', 
            'favorite_games', 'website', 'skype'
        ]

        widgets = {
            'birthdate': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_zodiac_sign(self): 
        '''Makes sure choosing "Aucun" in the zodiac sign's dropdown makes zodiac_sign NULL'''
        value = self.cleaned_data.get("zodiac_sign")
        if value == "":
            return None
        else:
            return value
        
    #TODO: add more tests!