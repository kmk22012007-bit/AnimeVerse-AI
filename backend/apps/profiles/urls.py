from django.urls import path
from apps.profiles.views import ProfileCurrentView, PublicUserProfileView

urlpatterns = [
    path('profile/', ProfileCurrentView.as_view(), name='profile-current'),
    path('users/<int:id>/', PublicUserProfileView.as_view(), name='user-public-profile'),
]
