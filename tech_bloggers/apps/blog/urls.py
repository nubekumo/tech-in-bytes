from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # Post listing and detail views
    path('', views.PostListView.as_view(), name='post_list'),
    path('liked/', views.LikedPostsView.as_view(), name='liked_posts'),
    path('<int:pk>-<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    
    # Post management
    path('create/', views.PostCreateView.as_view(), name='post_create'),
    path('manage/', views.PostManageView.as_view(), name='post_manage'),
    path('manage/<int:pk>-<slug:slug>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('manage/<int:pk>-<slug:slug>/publish/', views.PostPublishView.as_view(), name='post_publish'),
    path('manage/<int:pk>-<slug:slug>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    
    # Tags
    path('tags/', views.TagListView.as_view(), name='tag_list'),
    path('tags/<slug:tag_slug>/', views.TaggedPostListView.as_view(), name='tag_detail'),
    
    # Post interactions
    path('<int:pk>-<slug:slug>/like/', views.PostLikeView.as_view(), name='post_like'),
    path('<int:pk>-<slug:slug>/recommend/', views.PostRecommendView.as_view(), name='post_recommend'),
    path('<int:pk>-<slug:slug>/comment/', views.CommentCreateView.as_view(), name='comment_create'),
    path('comment/<int:pk>/reply/', views.CommentReplyView.as_view(), name='comment_reply'),
    
    # Image upload for TinyMCE
    path('upload-image/', views.ImageUploadView.as_view(), name='image_upload'),
    path('delete-image/', views.ImageDeleteView.as_view(), name='image_delete'),
]
