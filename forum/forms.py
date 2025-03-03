from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, TYPE_CHOICES, ZODIAC_CHOICES, GENDER_CHOICES, Topic, Post, Category

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
            'birthdate': forms.DateInput(attrs={'type': 'date'}), #TODO: [2] change this to a custom, worse dateinput
        }

    def clean_zodiac_sign(self): 
        '''Makes sure choosing "Aucun" in the zodiac sign's dropdown makes zodiac_sign NULL'''
        value = self.cleaned_data.get("zodiac_sign")
        if value == "":
            return None
        else:
            return value
        



class NewTopicForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 25}),
        label="Post Content",
        max_length=65535
    )

    class Meta:
        model = Topic
        fields = ['title', 'description']
        labels = {
            'title': 'Topic Title',
            'description': 'Short Description (optional)',
        }
        widgets = {
            'title': forms.TextInput(),
            'description': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.subforum = kwargs.pop('subforum', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        # Validate subforum exists and is a subforum
        if not self.subforum or not self.subforum.is_sub_forum:
            raise forms.ValidationError("Invalid subforum selected.")
        return cleaned_data

    def save(self, commit=True):
        # Create the topic with parent from subforum
        topic = super().save(commit=False)
        topic.author = self.user
        topic.parent = self.subforum  # Set parent from subforum parameter
        
        if commit:
            topic.save()
            # Create the initial post
            Post.objects.create(
                author=self.user,
                topic=topic,
                text=self.cleaned_data['text']
            )
        return topic