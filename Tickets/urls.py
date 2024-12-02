from django.urls import path

from . import views


urlpatterns = [
    path("", views.TicketsListAPIView.as_view()),
    path("<int:pk>/", views.TicketUpdateAPIView.as_view()),
    path("response/", views.OperatorReplyAPIView .as_view()),
]