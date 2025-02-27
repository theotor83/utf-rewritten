from django.test import TestCase
from django.urls import reverse
from forum.models import User, Profile, ForumGroup

# Create your tests here.

class RegisterFormTest(TestCase):
    
    def test_create_user_when_submitting_valid_form(self):
        form_data = {
            'username': 'dummy_user',
            'email': "valid@gmail.com",
            'password1': 'sUp73R__s3EcURe',
            'password2': 'sUp73R__s3EcURe',
            'birthdate': '2000-01-01',
            'type': 'neutral',
            'zodiac_sign': 'gemeaux',
            'gender': 'male',
            'desc': 'Dummy desc',
            'localisation': 'Dummy localisation',
            'loisirs': 'Dummy loisirs',
            'favorite_games': 'Dummy favorite games',
            'website': 'google.com',
            'skype': 'dummy_skype',
        }

        response = self.client.post(reverse('register'), data=form_data)
        self.assertTrue(User.objects.filter(username='dummy_user').exists())



    def test_create_profile_when_submitting_valid_form(self):
        form_data = {
            'username': 'dummy_user',
            'email': "valid@gmail.com",
            'password1': 'sUp73R__s3EcURe',
            'password2': 'sUp73R__s3EcURe',
            'birthdate': '2000-01-01',
            'type': 'neutral',
            'zodiac_sign': 'gemeaux',
            'gender': 'male',
            'desc': 'Dummy desc',
            'localisation': 'Dummy localisation',
            'loisirs': 'Dummy loisirs',
            'favorite_games': 'Dummy favorite games',
            'website': 'google.com',
            'skype': 'dummy_skype',
        }

        response = self.client.post(reverse('register'), data=form_data)
        self.assertTrue(Profile.objects.filter(website='google.com').exists())


    def test_link_profile_to_user_when_submitting_valid_form(self):
        form_data = {
            'username': 'dummy_user',
            'email': "valid@gmail.com",
            'password1': 'sUp73R__s3EcURe',
            'password2': 'sUp73R__s3EcURe',
            'birthdate': '2000-01-01',
            'type': 'neutral',
            'zodiac_sign': 'gemeaux',
            'gender': 'male',
            'desc': 'Dummy desc',
            'localisation': 'Dummy localisation',
            'loisirs': 'Dummy loisirs',
            'favorite_games': 'Dummy favorite games',
            'website': 'google.com',
            'skype': 'dummy_skype',
        }

        response = self.client.post(reverse('register'), data=form_data)
        if User.objects.filter(username='dummy_user').exists():
            linked_user = User.objects.get(username='dummy_user')
            self.assertTrue(Profile.objects.filter(user=linked_user).exists())
        else:
            self.assertTrue(False)


    def test_dont_create_user_when_submitting_invalid_user_form(self):
        form_data = {
            'username': 'dummy_user',
            'email': "valid@gmail.com",
            'password1': 'not_the',
            'password2': 'same_password',
            'birthdate': '2000-01-01',
            'type': 'neutral',
            'zodiac_sign': 'gemeaux',
            'gender': 'male',
            'desc': 'Dummy desc',
            'localisation': 'Dummy localisation',
            'loisirs': 'Dummy loisirs',
            'favorite_games': 'Dummy favorite games',
            'website': 'google.com',
            'skype': 'dummy_skype',
        }

        response = self.client.post(reverse('register'), data=form_data)
        self.assertFalse(User.objects.filter(username='dummy_user').exists())


    def test_dont_create_profile_when_submitting_invalid_user_form(self):
        form_data = {
            'username': 'dummy_user',
            'email': "valid@gmail.com",
            'password1': 'not_the',
            'password2': 'same_password',
            'birthdate': '2000-01-01',
            'type': 'neutral',
            'zodiac_sign': 'gemeaux',
            'gender': 'male',
            'desc': 'Dummy desc',
            'localisation': 'Dummy localisation',
            'loisirs': 'Dummy loisirs',
            'favorite_games': 'Dummy favorite games',
            'website': 'google.com',
            'skype': 'dummy_skype',
        }

        response = self.client.post(reverse('register'), data=form_data)
        self.assertFalse(Profile.objects.filter(website='google.com').exists())



    def test_dont_create_user_when_submitting_invalid_profile_form(self):
        form_data = {
            'username': 'dummy_user',
            'email': "valid@gmail.com",
            'password1': 'not_the',
            'password2': 'same_password',
            'birthdate': '2000-01-01',
            'type': 'neutral',
            'zodiac_sign': 'gemeaux',
            #missing gender
            'desc': 'Dummy desc',
            'localisation': 'Dummy localisation',
            'loisirs': 'Dummy loisirs',
            'favorite_games': 'Dummy favorite games',
            'website': 'google.com',
            'skype': 'dummy_skype',
        }

        response = self.client.post(reverse('register'), data=form_data)
        self.assertFalse(User.objects.filter(username='dummy_user').exists())


    def test_dont_create_profile_when_submitting_invalid_profile_form(self):
        form_data = {
            'username': 'dummy_user',
            'email': "valid@gmail.com",
            'password1': 'not_the',
            'password2': 'same_password',
            'birthdate': '2000-01-01',
            'type': 'neutral',
            'zodiac_sign': 'gemeaux',
            #missing gender
            'desc': 'Dummy desc',
            'localisation': 'Dummy localisation',
            'loisirs': 'Dummy loisirs',
            'favorite_games': 'Dummy favorite games',
            'website': 'google.com',
            'skype': 'dummy_skype',
        }

        response = self.client.post(reverse('register'), data=form_data)
        self.assertFalse(Profile.objects.filter(website='google.com').exists())


    def test_dont_create_user_or_profile_when_submitting_only_user_form(self):
        form_data = {
            'username': 'dummy_user',
            'email': "valid@gmail.com",
            'password1': 'sUp73R__s3EcURe',
            'password2': 'sUp73R__s3EcURe',
        }

        response = self.client.post(reverse('register'), data=form_data)
        self.assertFalse(User.objects.filter(username='dummy_user').exists())
        self.assertFalse(Profile.objects.exists())


    def test_dont_create_user_or_profile_when_submitting_only_profile_form(self):
        form_data = {
            'birthdate': '2000-01-01',
            'type': 'neutral',
            'zodiac_sign': 'gemeaux',
            'gender': 'male',
            'desc': 'Dummy desc',
            'localisation': 'Dummy localisation',
            'loisirs': 'Dummy loisirs',
            'favorite_games': 'Dummy favorite games',
            'website': 'google.com',
            'skype': 'dummy_skype',
        }

        response = self.client.post(reverse('register'), data=form_data)
        self.assertFalse(User.objects.filter(username='dummy_user').exists())
        self.assertFalse(Profile.objects.exists())

    def test_convert_zodiac_sign_to_null_when_selecting_Aucun(self):
        form_data = {
            'username': 'dummy_user',
            'email': "valid@gmail.com",
            'password1': 'sUp73R__s3EcURe',
            'password2': 'sUp73R__s3EcURe',
            'birthdate': '2000-01-01',
            'type': 'neutral',
            'zodiac_sign': "",
            'gender': 'male',
            'desc': 'Dummy desc',
            'localisation': 'Dummy localisation',
            'loisirs': 'Dummy loisirs',
            'favorite_games': 'Dummy favorite games',
            'website': 'google.com',
            'skype': 'dummy_skype',
        }

        response = self.client.post(reverse('register'), data=form_data)
        user_object = User.objects.get(username='dummy_user')
        self.assertEqual(user_object.profile.zodiac_sign, None)


    def test_type_is_neutral_when_not_selected(self):
        form_data = {
            'username': 'dummy_user',
            'email': "valid@gmail.com",
            'password1': 'sUp73R__s3EcURe',
            'password2': 'sUp73R__s3EcURe',
            'birthdate': '2000-01-01',
            #Nothing selected for type, should be neutral
            'zodiac_sign': "",
            'gender': 'male',
            'desc': 'Dummy desc',
            'localisation': 'Dummy localisation',
            'loisirs': 'Dummy loisirs',
            'favorite_games': 'Dummy favorite games',
            'website': 'google.com',
            'skype': 'dummy_skype',
        }

        response = self.client.post(reverse('register'), data=form_data)
        user_object = User.objects.get(username='dummy_user')
        self.assertEqual(user_object.profile.type, 'neutral')


    #TODO: add more tests!