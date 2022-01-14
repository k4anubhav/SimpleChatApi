from django.urls import path

from api.views import MemberView, ConversationView, login, ConversionBriefView

urlpatterns = [
    path('user/<int:member_id>/', MemberView.as_view()),
    path('conversation/', ConversionBriefView.as_view()),
    path('conversation/<int:pk>/', ConversationView.as_view()),
    path('login/', login),
]
