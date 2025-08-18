# forum/tests.py

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


class RestrictNewUsersTest(TestCase):
    """
    Test suite to ensure that when RESTRICT_NEW_USERS environment variable is False,
    new users can post freely across all forum areas.
    """
    
    def setUp(self):
        """Set up test data and ensure RESTRICT_NEW_USERS is False"""
        # Mock environment variable to False
        import os
        os.environ['RESTRICT_NEW_USERS'] = 'False'
        
        # Create required forum groups that are expected by the system
        self.fallen_child_group, _ = ForumGroup.objects.get_or_create(
            name="Fallen Child",
            defaults={
                'priority': 25, 
                'description': "Nouveaux sur le forum.",
                'is_staff_group': False, 
                'minimum_messages': 0, 
                'color': "#FFFFFF",
                'is_messages_group': True
            }
        )
        
        self.outsider_group, _ = ForumGroup.objects.get_or_create(
            name="Outsider",
            defaults={
                'priority': 15, 
                'description': "Membres ne s'étant pas encore présentés.",
                'is_staff_group': False, 
                'minimum_messages': 0, 
                'color': "#847B7E",
                'is_messages_group': True
            }
        )
        
        # Create 10 generic categories to avoid hardcoded assumptions
        self.categories = []
        for i in range(10):
            category = Category.objects.create(
                name=f"Generic Category {i+1}", 
                slug=f"generic-category-{i+1}"
            )
            self.categories.append(category)
        
        # Create 10 generic subforums distributed across categories
        from forum.models import Forum
        self.subforums = []
        setup_user = User.objects.create_user(username='setup_user', password='testpass123')
        Profile.objects.create(user=setup_user, birthdate='2000-01-01', gender='male')
        for i in range(10):
            category = self.categories[i % len(self.categories)]  # Distribute across categories
            subforum = Topic.objects.create(
                author=setup_user,
                title=f"Generic Subforum {i+1}",
                description=f"Generic subforum {i+1} for testing",
                category=category,
                is_sub_forum=True,
                slug=f"generic-subforum-{i+1}"
            )
            self.subforums.append(subforum)
        
        # Create 10 generic topics distributed across subforums
        self.topics = []
        for i in range(10):
            subforum = self.subforums[i % len(self.subforums)]  # Distribute across subforums
            topic = Topic.objects.create(
                author=setup_user,
                title=f"Generic Topic {i+1}",
                description=f"Generic topic {i+1} for testing",
                parent=subforum,
                slug=f"generic-topic-{i+1}"
            )
            # Create initial post for each topic
            Post.objects.create(
                author=setup_user,
                topic=topic,
                text=f"Initial post for Generic Topic {i+1}"
            )
            self.topics.append(topic)
        
        # Use items from the middle (8th items) to avoid any special handling of first items
        self.test_category = self.categories[7]    # 8th category
        self.test_subforum = self.subforums[7]     # 8th subforum  
        self.test_topic = self.topics[7]           # 8th topic
        
        # Also create a "Présentations" subforum for the specific presentations test
        self.presentations_subforum = Topic.objects.create(
            author=setup_user,
            title="Présentations",
            description="User presentations subforum",
            category=self.categories[2],  # Use 3rd category
            is_sub_forum=True,
            slug="presentations"
        )
        
        # Create dedicated test users for each test case - each user will only be used once
        # This ensures we're testing truly fresh users with no posting history
        self.test_users = {}
        test_cases = [
            'new_topic_get_subforum',
            'new_topic_get_category', 
            'new_post_get',
            'topic_details_get',
            'new_topic_post_subforum',
            'new_topic_post_category',
            'new_post_post',
            'topic_details_post',
            'presentations_post',
            'auth_redirect'
        ]
        
        for i, test_case in enumerate(test_cases):
            user = User.objects.create_user(
                username=f'fresh_user_{test_case}_{i}', 
                password='testpass123',
                email=f'fresh_user_{test_case}_{i}@test.com'
            )
            Profile.objects.create(
                user=user, 
                birthdate='2000-01-01', 
                gender='male'
            )
            self.test_users[test_case] = user

    def _set_classic_theme_cookie(self, response=None):
        """Helper method to set classic theme cookie"""
        if response:
            response.cookies['theme'] = 'classic'
        else:
            self.client.cookies['theme'] = 'classic'

    def test_new_topic_get_request_subforum_classic_theme(self):
        """Test GET request on /new_topic?f=[id] with classic theme - should not error"""
        user = self.test_users['new_topic_get_subforum']
        self.client.login(username=user.username, password='testpass123')
        self._set_classic_theme_cookie()
        
        response = self.client.get(f'/new_topic?f={self.test_subforum.id}')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Vous devez vous présenter")
        
        self.client.logout()

    def test_new_topic_get_request_category_classic_theme(self):
        """Test GET request on /new_topic?c=[id] with classic theme - should not error"""
        user = self.test_users['new_topic_get_category']
        self.client.login(username=user.username, password='testpass123')
        self._set_classic_theme_cookie()
        
        response = self.client.get(f'/new_topic?c={self.test_category.id}')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Vous devez vous présenter")
        
        self.client.logout()

    def test_new_post_get_request_classic_theme(self):
        """Test GET request on /new_post?t=[id] with classic theme - should not error"""
        user = self.test_users['new_post_get']
        self.client.login(username=user.username, password='testpass123')
        self._set_classic_theme_cookie()
        
        response = self.client.get(f'/new_post?t={self.test_topic.id}')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Vous devez vous présenter")
        
        self.client.logout()

    def test_topic_details_quick_reply_form_classic_theme(self):
        """Test GET request on /t[id]-[slug] shows quick reply form with classic theme"""
        user = self.test_users['topic_details_get']
        self.client.login(username=user.username, password='testpass123')
        self._set_classic_theme_cookie()
        
        response = self.client.get(f'/t{self.test_topic.id}-{self.test_topic.slug}')
        self.assertEqual(response.status_code, 200)
        # Check that quick reply form appears (look for common form elements)
        self.assertContains(response, 'name="text"')  # Quick reply text field
        self.assertNotContains(response, "Vous devez vous présenter")
        
        self.client.logout()

    def test_new_topic_post_request_subforum_classic_theme(self):
        """Test POST request on /new_topic?f=[id] creates topic successfully with classic theme"""
        user = self.test_users['new_topic_post_subforum']
        self.client.login(username=user.username, password='testpass123')
        self._set_classic_theme_cookie()
        
        # Count topics before
        initial_count = Topic.objects.filter(parent=self.test_subforum).count()
        
        response = self.client.post(f'/new_topic?f={self.test_subforum.id}', {
            'title': f'New Topic by {user.username}',
            'text': f'This is a new topic created by {user.username}',
            'icon': '',
        })
        
        # Should redirect to the new topic (successful creation)
        self.assertEqual(response.status_code, 302)
        
        # Verify topic was created
        final_count = Topic.objects.filter(parent=self.test_subforum).count()
        self.assertEqual(final_count, initial_count + 1)
        
        # Verify the topic exists
        new_topic = Topic.objects.filter(
            title=f'New Topic by {user.username}',
            parent=self.test_subforum
        ).first()
        self.assertIsNotNone(new_topic)
        self.assertEqual(new_topic.author, user)
        
        self.client.logout()

    def test_new_topic_post_request_category_classic_theme(self):
        """Test POST request on /new_topic?c=[id] creates topic successfully with classic theme"""
        user = self.test_users['new_topic_post_category']
        self.client.login(username=user.username, password='testpass123')
        self._set_classic_theme_cookie()
        
        # Count topics before
        initial_count = Topic.objects.filter(category=self.test_category).count()
        
        response = self.client.post(f'/new_topic?c={self.test_category.id}', {
            'title': f'Category Topic by {user.username}',
            'text': f'This is a category topic created by {user.username}',
            'icon': '',
        })
        
        # Should redirect to the new topic (successful creation)
        self.assertEqual(response.status_code, 302)
        
        # Verify topic was created
        final_count = Topic.objects.filter(category=self.test_category).count()
        self.assertEqual(final_count, initial_count + 1)
        
        # Verify the topic exists
        new_topic = Topic.objects.filter(
            title=f'Category Topic by {user.username}',
            category=self.test_category
        ).first()
        self.assertIsNotNone(new_topic)
        self.assertEqual(new_topic.author, user)
        
        self.client.logout()

    def test_new_post_post_request_classic_theme(self):
        """Test POST request on /new_post?t=[id] creates post successfully with classic theme"""
        user = self.test_users['new_post_post']
        self.client.login(username=user.username, password='testpass123')
        self._set_classic_theme_cookie()
        
        # Count posts before
        initial_count = Post.objects.filter(topic=self.test_topic).count()
        
        response = self.client.post(f'/new_post?t={self.test_topic.id}', {
            'text': f'This is a new post by {user.username}',
        })
        
        # Should redirect to the topic (successful creation)
        self.assertEqual(response.status_code, 302)
        
        # Verify post was created
        final_count = Post.objects.filter(topic=self.test_topic).count()
        self.assertEqual(final_count, initial_count + 1)
        
        # Verify the post exists
        new_post = Post.objects.filter(
            text=f'This is a new post by {user.username}',
            topic=self.test_topic
        ).first()
        self.assertIsNotNone(new_post)
        self.assertEqual(new_post.author, user)
        
        self.client.logout()

    def test_topic_details_quick_reply_post_classic_theme(self):
        """Test POST request on /t[id]-[slug] creates post via quick reply with classic theme"""
        user = self.test_users['topic_details_post']
        self.client.login(username=user.username, password='testpass123')
        self._set_classic_theme_cookie()
        
        # Count posts before
        initial_count = Post.objects.filter(topic=self.test_topic).count()
        
        response = self.client.post(f'/t{self.test_topic.id}-{self.test_topic.slug}', {
            'text': f'Quick reply by {user.username}',
            'reply': 'Submit',  # Add the reply parameter expected by the form
        })
        
        # Should redirect to the new post (successful creation)
        self.assertEqual(response.status_code, 302)
        
        # Verify post was created
        final_count = Post.objects.filter(topic=self.test_topic).count()
        self.assertEqual(final_count, initial_count + 1)
        
        # Verify the post exists
        new_post = Post.objects.filter(
            text=f'Quick reply by {user.username}',
            topic=self.test_topic
        ).first()
        self.assertIsNotNone(new_post)
        self.assertEqual(new_post.author, user)
        
        self.client.logout()

    def test_new_users_can_post_in_presentations_subforum(self):
        """Test that new users can post in Présentations subforum when RESTRICT_NEW_USERS=False"""
        user = self.test_users['presentations_post']
        self.client.login(username=user.username, password='testpass123')
        self._set_classic_theme_cookie()
        
        # Count topics before
        initial_count = Topic.objects.filter(parent=self.presentations_subforum).count()
        
        response = self.client.post(f'/new_topic?f={self.presentations_subforum.id}', {
            'title': f'Presentation by {user.username}',
            'text': f'Hello, I am {user.username}',
            'icon': '',
        })
        
        # Should redirect to the new topic (successful creation)
        self.assertEqual(response.status_code, 302)
        
        # Verify topic was created
        final_count = Topic.objects.filter(parent=self.presentations_subforum).count()
        self.assertEqual(final_count, initial_count + 1)
        
        self.client.logout()

    def test_unauthenticated_users_redirected_to_login(self):
        """Test that unauthenticated users are redirected to login page"""
        # Test various endpoints without authentication
        endpoints = [
            f'/new_topic?f={self.test_subforum.id}',
            f'/new_topic?c={self.test_category.id}',
            f'/new_post?t={self.test_topic.id}',
        ]
        
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                # Just check that it redirects to login, don't be strict about the next parameter
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/login/'))

    def tearDown(self):
        """Clean up after tests"""
        # Reset environment variable
        import os
        if 'RESTRICT_NEW_USERS' in os.environ:
            del os.environ['RESTRICT_NEW_USERS']