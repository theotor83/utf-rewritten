from django.test import TestCase, SimpleTestCase
from django.urls import reverse
from forum.models import User, Profile, ForumGroup, Topic, Category, Post
from django.core.exceptions import ValidationError
from .forms import ProfileForm

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


    def test_assigned_to_outsider_when_registering(self):
        ForumGroup.objects.create(name = "Outsider", priority = 10, description = """Membres ne s'étant pas encore présentés.
        Nombre de messages : 0.""", is_staff_group = False, minimum_messages = 0, color="#FFFFFF")
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
        user_object = User.objects.get(username='dummy_user')
        self.assertEqual(user_object.profile.get_top_group.name, 'Outsider')


    def test_return_500_when_outsider_doesnt_exist(self):
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
        user_object = User.objects.get(username='dummy_user')
        self.assertEqual(response.status_code, 500)


class ProfilePageTest(TestCase):

    def test_redirect_to_error_page_when_accessing_broken_profile_url(self):
        response = self.client.post(reverse('profile-details', args=["999999"]))
        self.assertContains(response, "Informations")
        self.assertContains(response, "mais cet utilisateur")
        self.assertContains(response, "existe pas.")
        self.assertTemplateUsed(response, "error_page.html")
        self.assertTemplateNotUsed(response, "profile_page.html")
        self.assertTemplateNotUsed(response, "member_not_found.html")

    #TODO: [2] Add more tests


class TopicModelTest(TestCase):
    def test_index_topic_cannot_have_parent(self):
        parent_topic = Topic.objects.create(title="Parent")
        topic = Topic(is_index_topic=True, parent=parent_topic)
        with self.assertRaises(ValidationError):
            topic.full_clean()

    def test_category_sync_with_parent(self):
        category = Category.objects.create(name="Test Category")
        parent_topic = Topic.objects.create(title="Parent", category=category)
        child_topic = Topic.objects.create(title="Child", parent=parent_topic)
        self.assertEqual(child_topic.category, category)


class ForumGroupModelTest(TestCase):
    def test_group_ordering(self):
        group1 = ForumGroup.objects.create(name="Group A", priority=10, description="Desc A", minimum_messages=0)
        group2 = ForumGroup.objects.create(name="Group B", priority=20, description="Desc B", minimum_messages=0)
        group3 = ForumGroup.objects.create(name="Group C", priority=15, description="Desc C", minimum_messages=0)

        groups = ForumGroup.objects.all()
        self.assertEqual(groups[0].name, "Group B")
        self.assertEqual(groups[1].name, "Group C")
        self.assertEqual(groups[2].name, "Group A")

class ProfileModelTest(TestCase):
    def test_get_top_group(self):
        user = User.objects.create(username="test_user")
        profile = Profile.objects.create(user=user, birthdate="2000-01-01", gender="male")

        group1 = ForumGroup.objects.create(name="Group A", priority=10, description="Desc A", minimum_messages=0)
        group2 = ForumGroup.objects.create(name="Group B", priority=20, description="Desc B", minimum_messages=0)
        profile.groups.add(group1, group2)

        self.assertEqual(profile.get_top_group.name, "Group B")

    def test_profile_str_representation(self):
        user = User.objects.create(username="str_test")
        profile = Profile.objects.create(user=user, birthdate="2000-01-01", gender="male")
        self.assertEqual(str(profile), "str_test's profile")

    def test_user_profile_cascade_delete(self):
        user = User.objects.create_user(username="delete_test")
        Profile.objects.create(user=user, birthdate="2000-01-01", gender="male")
        user.delete()
        self.assertFalse(Profile.objects.exists())

class PostModelTest(TestCase):
    def test_post_author_set_null_on_user_delete(self):
        user = User.objects.create(username="test_user")
        profile = Profile.objects.create(user=user, birthdate="2000-01-01", gender="male")
        post = Post.objects.create(author=user, text="Test post")
        user.delete()
        post.refresh_from_db()
        self.assertIsNone(post.author)

class ProfileFormTest(TestCase):
    def test_zodiac_sign_empty_string_converts_to_null(self):
        form_data = {
            'username': 'test_user',
            'email': 'test@example.com',
            'password1': 'sUp73R__s3EcURe',
            'password2': 'sUp73R__s3EcURe',
            'birthdate': '2000-01-01',
            'gender': 'male',
            'zodiac_sign': '',  # Empty string
        }
        form = ProfileForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data['zodiac_sign'])

    def test_form_widget_functionality(self):
        form = ProfileForm()
        widget_html = form['gender'].as_widget()
        self.assertIn('<option disabled', widget_html)

class ForumGroupModelTest(TestCase):
    def test_unique_group_name(self):
        ForumGroup.objects.create(name="Unique Group", priority=10, description="Desc", minimum_messages=0)
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            ForumGroup.objects.create(name="Unique Group", priority=20, description="Desc", minimum_messages=0)

    def test_unique_group_priority(self):
        ForumGroup.objects.create(name="Group A", priority=10, description="Desc", minimum_messages=0)
        with self.assertRaises(Exception):  # IntegrityError or ValidationError
            ForumGroup.objects.create(name="Group B", priority=10, description="Desc", minimum_messages=0)

class LoginLogoutViewTest(TestCase):
    def test_successful_login(self):
        user = User.objects.create_user(username="test_user", password="sUp73R__s3EcURe")
        response = self.client.post(reverse('login-view'), {'username': 'test_user', 'password': 'sUp73R__s3EcURe'})
        self.assertRedirects(response, reverse('index'))

    def test_logout(self):
        user = User.objects.create_user(username="test_user", password="sUp73R__s3EcURe")
        self.client.login(username="test_user", password="sUp73R__s3EcURe")
        response = self.client.get(reverse('logout-view'))
        self.assertRedirects(response, reverse('index'))

class ProfileFormTest(TestCase):
    def test_required_fields(self):
        form_data = {
            'birthdate': '2000-01-01',
            'gender': '',  # Missing required field
        }
        form = ProfileForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('gender', form.errors)

    def test_optional_fields(self):
        form_data = {
            'birthdate': '2000-01-01',
            'gender': 'male',
            'zodiac_sign': '',  # Optional field
        }
        form = ProfileForm(data=form_data)
        self.assertTrue(form.is_valid())

class URLTest(TestCase):
    def test_profile_url_resolution(self):
        path = reverse('profile-details', args=[1])
        self.assertEqual(path, '/profile/1/')

class ViewAuthorizationTest(TestCase):
    def test_register_view_requires_no_auth(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Logout")


class TopicIndexTest(TestCase):
    def test_index_topic_added_to_category(self):
        category = Category.objects.create(name="Test Category")

        # Create a topic with is_index_topic=True
        user = User.objects.create_user(username="testuser", password="testpass")
        topic = Topic.objects.create(
            author=user,
            title="Index Topic",
            is_index_topic=True,
            category=category
        )
        self.assertIn(topic, category.index_topics.all())
    
    def test_non_index_topic_not_added(self):
        category = Category.objects.create(name="Test Category")
        user = User.objects.create_user(username="testuser", password="testpass")
        topic = Topic.objects.create(
            author=user,
            title="Non-Index Topic",
            is_index_topic=False,
            category=category
        )
        self.assertNotIn(topic, category.index_topics.all())

    def test_update_to_index_topic(self):
        category = Category.objects.create(name="Test Category")
        user = User.objects.create_user(username="testuser", password="testpass")
        topic = Topic.objects.create(
            author=user,
            title="Update Test",
            is_index_topic=False,
            category=category
        )
        # Update to index topic
        topic.is_index_topic = True
        topic.save()
        self.assertIn(topic, category.index_topics.all())