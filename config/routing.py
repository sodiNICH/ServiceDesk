from django.urls import re_path

from Tickets.consumers import TicketListConsumer, TicketMessageConsumer


websocket_urlpatterns = [
    re_path(
        r"ws/ticket_list/$",
        TicketListConsumer.as_asgi(),
    ),
    re_path(
        r"ws/ticket_message/(?P<ticket_id>\d+)/",
        TicketMessageConsumer.as_asgi(),
    ),
]
