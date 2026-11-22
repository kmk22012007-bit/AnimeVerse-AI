from django.urls import path
from apps.profiles.views import (
    ProfileCurrentView,
    ProfilePreferencesView,
    ProfileTasteProfileView,
    PublicUserProfileView,
    UserFollowActionView,
    UserFollowersListView,
    UserFollowingListView,
)

urlpatterns = [
    path('profile/', ProfileCurrentView.as_view(), name='profile-current'),
    path('profile/preferences/', ProfilePreferencesView.as_view(), name='profile-preferences'),
    path('profile/taste-profile/', ProfileTasteProfileView.as_view(), name='profile-taste-profile'),
    path('users/<int:id>/', PublicUserProfileView.as_view(), name='user-public-profile'),
    path('users/<int:id>/follow/', UserFollowActionView.as_view(), name='user-follow-action'),
    path('users/<int:id>/followers/', UserFollowersListView.as_view(), name='user-followers-list'),
    path('users/<int:id>/following/', UserFollowingListView.as_view(), name='user-following-list'),
]
