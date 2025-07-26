# forum/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, TYPE_CHOICES, ZODIAC_CHOICES, GENDER_CHOICES, Topic, Post, Category, ICON_CHOICES, PrivateMessageThread, PrivateMessage
from PIL import Image
from io import BytesIO
import os
from django.core.files.base import ContentFile
from .widgets import IconRadioSelect

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
            'favorite_games', 'website', 'skype', 'profile_picture', 'signature'
        ]

        widgets = { #TODO: [2] change this to a custom, worse dateinput
            'birthdate': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date'}
            ),
        }

    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if 'profile_picture' in self.files:
            img_file = self.cleaned_data['profile_picture']
            img_file.seek(0)
            img = Image.open(img_file)
            original_width, original_height = img.width, img.height

            # Check if resizing is needed
            if original_width > 200 or original_height > 250:
                # Calculate ratios for both dimensions
                width_ratio = 200 / original_width
                height_ratio = 250 / original_height
                
                # Use the smaller ratio to maintain aspect ratio
                resize_ratio = min(width_ratio, height_ratio)
                
                new_width = int(original_width * resize_ratio)
                new_height = int(original_height * resize_ratio)
                output_size = (new_width, new_height)

                # Resize with high-quality filter
                img = img.resize(output_size, Image.Resampling.LANCZOS)

                # Handle image format and color mode
                img_format = img.format or 'JPEG'
                if img_format in ('JPEG', 'JPG'):
                    img_format = 'JPEG'
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                elif img_format == 'PNG':
                    if img.mode not in ('RGBA', 'LA'):
                        img = img.convert('RGBA')
                else:
                    img_format = 'JPEG'
                    img = img.convert('RGB')

                # Save to buffer
                buffer = BytesIO()
                img.save(buffer, format=img_format)
                buffer.seek(0)

                # Generate filename
                original_name = os.path.splitext(img_file.name)[0]
                new_filename = f"{original_name}_resized.{img_format.lower()}"

                # Replace original image
                profile.profile_picture.save(
                    new_filename,
                    ContentFile(buffer.read()),
                    save=False
                )
            else:
                pass # No resizing needed, just save the original image

            profile.upload_size += profile.profile_picture.size

        if commit:
            profile.save()
        return profile

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
    icon = forms.ChoiceField(
        choices=ICON_CHOICES,
        widget=IconRadioSelect, # Use the custom widget here!
        label="Select Topic Icon",
        required=False
    )

    class Meta:
        model = Topic
        fields = ['title', 'description', 'icon']
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
        # This might be a Category object or a Subforum object, depending on the context
        parent_object = self.subforum

        if not parent_object:
            raise forms.ValidationError("Un forum ou une catégorie invalide a été sélectionné(e).")
        
        is_subforum = isinstance(parent_object, Topic)
        is_category = isinstance(parent_object, Category)

        if not is_subforum and not is_category:
             raise forms.ValidationError("La cible sélectionnée n'est ni un forum ni une catégorie valide.")
        
        # Specific validation for subforums
        if is_subforum:
            if not parent_object.is_sub_forum:
                 raise forms.ValidationError("Un sujet invalide a été sélectionné.")
            if parent_object.is_locked:
                if not self.user.profile.is_user_staff:
                    raise forms.ValidationError("Ce forum est verrouillé.")
            if self.user.profile.get_top_group == 'Outsider' and parent_object.id != 1:
                raise forms.ValidationError("Vous devez vous présenter avant de poster dans ce forum.")

        if title is None or title.strip() == '':
            raise forms.ValidationError("Vous devez entrer un titre avant de poster.")

        if len(title) <= 1 or len(title) > 60:
            raise forms.ValidationError("La longueur du titre de ce sujet doit être comprise entre 1 et 60 caractères")

        # General validation applicable to both
        if self.user.profile.get_top_group == 'Outsider' and (not is_subforum or parent_object.id != 1):
             # Allow posting in 'presentations' subforum, but restrict elsewhere if Outsider
             # If posting directly in a category as an Outsider, restrict it.
             if is_category:
                 raise forms.ValidationError("Vous devez vous présenter avant de poster dans cette catégorie.")

        return cleaned_data

    def save(self, commit=True):
        # Create the topic with parent from subforum
        topic = super().save(commit=False)
        topic.author = self.user
        #topic.parent = self.subforum  # Set parent from subforum parameter
        topic.icon = self.cleaned_data.get('icon')
        #print(self.cleaned_data.get('icon'))

        parent_object = self.subforum # This could be a Subforum (Topic) or a Category

        if isinstance(parent_object, Topic) and parent_object.is_sub_forum:
            topic.parent = parent_object  # Set parent subforum
            topic.category = parent_object.category # Get category from parent subforum
        elif isinstance(parent_object, Category):
            topic.parent = None # No parent subforum when posting directly to category
            topic.category = parent_object # Set category directly
        else:
            # Should not reach here if validation is correct
            raise ValueError("Invalid parent object type during save.")
        
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
            if self.user.profile.is_user_staff:
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
    

class QuickReplyForm(forms.ModelForm):
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
            'text': forms.Textarea(
                attrs={'rows': 7,}),
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
            if self.user.profile.is_user_staff:
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
    
class MemberSortingForm(forms.Form):
    mode = forms.ChoiceField(
        choices=[
            ('joined', 'Inscrit le'),
            ('lastvisit', 'Dernière visite'),
            ('username', 'Nom d’utilisateur'),
            ('posts', 'Messages'),
            ('email', 'E-mail'),
            ('website', 'Site Web'),
            ('topten', 'Top 10 des Posteurs'),
        ],
        initial='joined',
        label='',
        widget=forms.Select(attrs={'id': None}),  # Removes the 'id' attribute
    )
    order = forms.ChoiceField(
        choices=[
            ('ASC', 'Croissant'),
            ('DESC', 'Décroissant'),
        ],
        initial='ASC',
        label='',
        widget=forms.Select(attrs={'id': None}),  # Removes the 'id' attribute
    )

class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']

class RecentTopicsForm(forms.Form):
    days = forms.ChoiceField(   
        choices=[
            ('0', 'Tous les sujets'),
            ('1', '1 Jour'),
            ('7', '7 Jours'),
            ('14', '2 Semaines'),
            ('30', '1 Mois'),
            ('90', '3 Mois'),
            ('180', '6 Mois'),
            ('365', '1 An'),
        ],
        initial='0',
        label='RecentTopicLabel',
        widget=forms.Select(attrs={'id': None}),
    )

class RecentPostsForm(forms.Form):
    days = forms.ChoiceField(   
        choices=[
            ('0', 'Tous les sujets'),
            ('1', '1 Jour'),
            ('7', '7 Jours'),
            ('14', '2 Semaines'),
            ('30', '1 Mois'),
            ('90', '3 Mois'),
            ('180', '6 Mois'),
            ('365', '1 An'),
        ],
        initial='0',
        label='RecentTopicLabel',
        widget=forms.Select(attrs={'id': None}),
    )
    order = forms.ChoiceField(
        choices=[
            ('ASC', 'Croissant'),
            ('DESC', 'Décroissant'),
        ],
        initial='ASC',
        label='',
        widget=forms.Select(attrs={'id': None}),  # Removes the 'id' attribute
    )

class PollForm(forms.Form):
    question = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'maxlength': '255',
            'style': 'width:450px !important',
        }),
        required=False,
    )
    options = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': '10',
            'cols': '40',
            'style': 'width:450px !important',
        }),
        required=False,
    )
    days_to_vote = forms.IntegerField(
        min_value=0,
        widget=forms.TextInput(attrs={
            'size': '3',
            'maxlength': '3',
            'style': 'width:30px !important',
        }),
        required=False,  # Empty = 0 days (infinite)
    )
    multiple_choice = forms.ChoiceField(
        choices=(
            (-1, "Yes"),
            (1, "No")
        ),
        widget=forms.RadioSelect,
        initial=1  # "No" as the default
    )
    can_change_vote = forms.ChoiceField(
        choices=(
            (1, "Yes"),
            (0, "No")
        ),
        widget=forms.RadioSelect,
        initial=1  # "No" as the default
    )
    
    def clean_options(self):
        data = self.cleaned_data.get("options")
        # Split the options by newline and filter out empty strings
        option_list = [opt.strip() for opt in data.splitlines() if opt.strip()]
        if len(option_list) < 2:
            raise forms.ValidationError("Votre sondage doit contenir au moins 2 options.")
        if len(option_list) > 10:
            raise forms.ValidationError("Votre sondage ne peut pas contenir plus de 10 options.")
        return option_list
    
    def clean_days_to_vote(self):
        data = self.cleaned_data.get('days_to_vote')
        if data is None:  # If the field is empty, we want to set it to 0 for infinite
            return 0
        return data
    
class PollVoteFormUnique(forms.Form):
    options = forms.ChoiceField(
        widget=forms.RadioSelect,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        poll_options = kwargs.pop('poll_options', [])
        super().__init__(*args, **kwargs)
        self.fields['options'].choices = [(opt.id, opt.text) for opt in poll_options]
    
class PollVoteFormMultiple(forms.Form):
    options = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        poll_options = kwargs.pop('poll_options', [])
        super().__init__(*args, **kwargs)
        self.fields['options'].choices = [(opt.id, opt.text) for opt in poll_options]

class NewPMThreadForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 25}),
        label="Message Content",
        max_length=65535
    )
    recipient = forms.CharField(
        widget=forms.TextInput(),
        label="Recipient's Username",
        max_length=150
    )

    class Meta:
        model = PrivateMessageThread
        fields = ['title']
        labels = {
            'title': "Subject",
        }
        widgets = {
            'title': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_recipient(self):
        recipient_username = self.cleaned_data.get('recipient')
        if not recipient_username:
            raise forms.ValidationError("Vous devez spécifier un destinataire.")
        
        try:
            recipient_user = User.objects.get(username=recipient_username)
        except User.DoesNotExist:
            raise forms.ValidationError("Cet utilisateur n'existe pas.")
        
        if recipient_user == self.user:
            raise forms.ValidationError("Vous ne pouvez pas vous envoyer un message à vous-même.")
        
        return recipient_user

    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get('text')
        title = cleaned_data.get('title')

        if not title or title.strip() == '':
            raise forms.ValidationError("Vous devez entrer un sujet.")

        if len(title) < 1 or len(title) > 255:
            raise forms.ValidationError("La longueur du sujet doit être comprise entre 1 et 255 caractères")

        if text is None or text.strip() == '':
            raise forms.ValidationError("Vous devez entrer un message avant de poster.")

        if len(text) < 1 or len(text) > 50000:
            raise forms.ValidationError("La longueur du message doit être comprise entre 1 et 50000 caractères")

        return cleaned_data
    
    def save(self, commit=True):
        # Create the PM thread with recipient and user
        pm_thread = super().save(commit=False)
        pm_thread.author = self.user
        pm_thread.recipient = self.cleaned_data['recipient']

        if commit:
            pm_thread.save()
            # Create the initial PM message
            PrivateMessage.objects.create(
                thread=pm_thread,
                author=self.user,
                recipient=self.cleaned_data['recipient'],
                text=self.cleaned_data['text']
            )
        return pm_thread