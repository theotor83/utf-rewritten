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
        title = cleaned_data.get('title')

        # Validate subforum exists and is a subforum
        if not self.subforum or not self.subforum.is_sub_forum:
            raise forms.ValidationError("Un sujet invalide a été sélectionné.")
        
        if title is None or title.strip() == '':
            raise forms.ValidationError("Vous devez entrer un titre avant de poster.")
        
        if len(title) < 10 or len(title) > 60:
            raise forms.ValidationError("La longueur du titre de ce sujet doit être comprise entre 10 et 60 caractères")
        
        if self.subforum.is_locked:
            if self.user.is_user_staff:
                return cleaned_data
            raise forms.ValidationError("Ce topic est verrouillé.")

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
    
class NewPostForm(forms.ModelForm):
    # Read-only fields for topic context
    topic_title = forms.CharField(
        disabled=True,
        required=False,
        label="Topic Title"
    )
    topic_description = forms.CharField(
        disabled=True,
        required=False,
        label="Topic Description"
    )

    class Meta:
        model = Post
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 25}),
        }
        labels = {
            'text': 'Post Content',
        }

    def __init__(self, *args, **kwargs):
        self.topic = kwargs.pop('topic', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial values for read-only fields
        if self.topic:
            self.fields['topic_title'].initial = self.topic.title
            self.fields['topic_description'].initial = self.topic.description

        self.fields['text'].initial = '' # Clear the text field to remove DEFAULT POST TEXT

    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get('text')

        # Validate topic exists and is a topic
        if not self.topic or self.topic.is_sub_forum:
            raise forms.ValidationError("Un sujet invalide a été sélectionné.")
        
        if not self.user:
            raise forms.ValidationError("Cet utilisateur n'existe pas.")
        
        if not text or text.strip() == '':
            raise forms.ValidationError("Vous devez entrer un message avant de poster.")
        
        if self.topic.is_locked:
            if self.user.is_user_staff:
                return cleaned_data
            raise forms.ValidationError("Ce sujet est verrouillé.")
        
        return cleaned_data

    def save(self, commit=True):
        # Create post with user and topic relationship
        post = super().save(commit=False)
        post.author = self.user
        post.topic = self.topic
        
        if commit:
            post.save()
        return post