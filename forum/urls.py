from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index_redirect, name='index-redirect'),
    path('index/', views.index, name='index'),
    path('faq/', views.faq, name='faq'),
    path('register/regulation/', views.register_regulation, name='register-regulation'),
    path('register/', views.register, name='register'),
    #path('member_not_found/', views.member_not_found, name='member-not-found'),
    path('login/', views.login_view, name='login-view'),
    path('logout/', views.logout_view, name='logout-view'),
    path('profile/<int:userid>/', views.profile_details, name='profile-details'),
    path('memberlist', views.member_list, name='member-list'),
    path('f<int:subforumid>-<slug:subforumslug>', views.subforum_details, name='subforum-details'),
    path('t<int:topicid>-<slug:topicslug>', views.topic_details, name='topic-details'),
    path('testpage', views.test_page, name='test-page'),
    path('new_topic', views.new_topic, name='new-topic'),
    path('new_post', views.new_post, name='new-post'),
    path('c<int:categoryid>-<slug:categoryslug>', views.category_details, name='category-details'),
    path('search/', views.search, name='search'),
    path('edit_profile/', views.edit_profile, name='edit-profile'),
    path('search_results', views.search_results, name='search-results'),
    path('debug-csrf/', views.debug_csrf, name='debug-csrf'),
    path('edit_post/<int:postid>/', views.edit_post, name='edit-post'),
    path('groups/', views.groups, name='groups'),
    path('groups/g<int:groupid>', views.groups_details, name='groups-details'),
    path('mark_as_read', views.mark_as_read, name='mark-as-read'),
    path('p<int:postid>', views.post_redirect, name='post-redirect'),
    path('post-preview', views.post_preview, name='post-preview'),
    path('jumpbox/', views.jumpbox_redirect, name='jumpbox-redirect'),
    path('prefill_new_post', views.prefill_new_post, name='prefill-new-post'),
    path('viewonline/', views.viewonline, name='viewonline'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)