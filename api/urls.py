from django.urls import path

from api.views import MemberView, ConversationView, login

urlpatterns = [
    path('user/', MemberView.as_view()),
    path('conversation/', ConversationView.as_view()),
    path('conversation/<int:pk>/', ConversationView.as_view()),
    path('login/', login),
]
