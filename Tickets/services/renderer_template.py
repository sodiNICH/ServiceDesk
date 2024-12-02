from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin

class TicketListTemplate(UserPassesTestMixin, TemplateView):
    template_name = "list_tickets.html"

    def test_func(self):
        return self.request.user.is_staff


class TicketDetailTemplate(UserPassesTestMixin, TemplateView):
    template_name = "detail_ticket.html"

    def test_func(self):
        return self.request.user.is_staff
