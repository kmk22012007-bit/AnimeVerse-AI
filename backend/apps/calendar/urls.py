from django.urls import path
from apps.calendar.views import CalendarSeasonView, CalendarUpcomingView

urlpatterns = [
    path('season/', CalendarSeasonView.as_view(), name='calendar-season'),
    path('upcoming/', CalendarUpcomingView.as_view(), name='calendar-upcoming'),
]
