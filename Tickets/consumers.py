"""
Consumer for async Websocket
"""

import json
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer


logger = logging.getLogger(__name__)


class TicketListConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "ticket_list",
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            "ticket_list",
            self.channel_name,
        )

    async def add_ticket(self, event):
        ticket_data: dict = event["ticket"]
        logger.info(f"Новое обращение ID: {ticket_data['id']}")
        await self.send(
            text_data=json.dumps(ticket_data),
        )


class TicketMessageConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.ticket_id = self.scope['url_route']['kwargs']['ticket_id']
        await self.channel_layer.group_add(
            f"ticket_message_{self.ticket_id}",
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            f"ticket_message_{self.ticket_id}",
            self.channel_name,
        )

    async def add_message_in_ticket(self, event):
        ticket_message: str = event["ticket_message"]
        logger.info(f"Новое сообщение: {ticket_message}")
        await self.send(
            text_data=json.dumps(ticket_message),
        )
