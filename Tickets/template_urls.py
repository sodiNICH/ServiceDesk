from django.urls import path
from .services import renderer_template


urlpatterns = [
    path("", renderer_template.TicketListTemplate.as_view()),
    path("<int:pk>/", renderer_template.TicketDetailTemplate.as_view()),
]
