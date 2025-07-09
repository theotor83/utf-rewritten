from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.cache import cache_page
from debug_toolbar.toolbar import debug_toolbar_urls

app_name = 'archive'

urlpatterns = [
    path('', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.index_redirect), name='index-redirect'),
    path('index/', cache_page(60*60)(views.index), name='index'),
    path('faq/', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.faq), name='faq'),
    path('register/regulation/', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.register_regulation), name='register-regulation'),
    path('register/', views.register, name='register'),
    #path('member_not_found/', views.member_not_found, name='member-not-found'),
    path('login/', views.login_view, name='login-view'),
    path('logout/', views.logout_view, name='logout-view'),
    path('profile/<int:userid>/', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.profile_details), name='profile-details'),
    path('memberlist', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.member_list), name='member-list'),
    path('f<int:subforum_display_id>-<slug:subforumslug>', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.subforum_details), name='subforum-details'),
    path('t<int:topicid>-<slug:topicslug>', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.topic_details), name='topic-details'),
    path('testpage', views.test_page, name='test-page'),
    path('new_topic', views.new_topic, name='new-topic'),
    path('new_post', views.new_post, name='new-post'),
    path('c<int:categoryid>-<slug:categoryslug>', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.category_details), name='category-details'),
    path('search/', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.search), name='search'),
    path('edit_profile/', views.edit_profile, name='edit-profile'),
    path('search_results', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.search_results), name='search-results'),
    path('debug-csrf/', views.debug_csrf, name='debug-csrf'),
    path('edit_post/<int:postid>/', views.edit_post, name='edit-post'),
    path('groups/', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.groups), name='groups'),
    path('groups/g<int:groupid>', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.groups_details), name='groups-details'),
    path('mark_as_read', views.mark_as_read, name='mark-as-read'),
    path('p<int:postid>', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.post_redirect), name='post-redirect'),
    path('post-preview', views.post_preview, name='post-preview'),
    path('jumpbox/', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.jumpbox_redirect), name='jumpbox-redirect'),
    path('prefill_new_post', views.prefill_new_post, name='prefill-new-post'),
    path('viewonline/', cache_page(settings.ARCHIVE_CACHE_TIMEOUT)(views.viewonline), name='viewonline'),
    path('removevotes/<int:pollid>', views.removevotes, name='removevotes'),
]# + debug_toolbar_urls()

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 