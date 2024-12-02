import logging

from rest_framework import status, generics
from rest_framework.permissions import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from .models import Tickets
from .serializers import TicketsSerializer
from .services.tasks_runner import start_tasks_send_mail


logger = logging.getLogger(__name__)


class TicketsListAPIView(generics.ListAPIView):
    queryset = Tickets.objects.all()
    serializer_class = TicketsSerializer
    permission_classes = (IsAdminUser,)
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filterset_fields = ["status"]
    ordering_fields = ["status", "created_at"]
    ordering = ["created_at"]

    @swagger_auto_schema(
        operation_description="Получение списка обращений с фильтрацией по статусу и сортировкой.",
        manual_parameters=[
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                description="Фильтр по статусу обращения (например, 'new' или 'process').",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "ordering",
                openapi.IN_QUERY,
                description="Сортировка по полям, например 'status' или '-created_at' (по убыванию).",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={200: TicketsSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        """
        Возвращает список обращений с возможностью фильтрации и сортировки.
        """
        return self.list(request, *args, **kwargs)


class TicketUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = Tickets.objects.all()
    serializer_class = TicketsSerializer
    permission_classes = (IsAdminUser,)

    def patch(self, request, *args, **kwargs):
        """
        Обновляет данные обращения.
        """
        return self.partial_update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        ticket = self.get_object()
        if request.data.get("status") == "closed":
            start_tasks_send_mail(
                ticket,
                subject=f"Проблема №{ticket.id} решена",
                body="Ваша проблема решена",
            )
        return super().partial_update(request, *args, **kwargs)


class OperatorReplyAPIView(APIView):
    permission_classes = (IsAdminUser,)

    @swagger_auto_schema(
        operation_description="Ответ пользователю на обращение.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "message": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Текст сообщения для пользователя.",
                ),
                "ticket_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID обращения, для которого отправляется сообщение.",
                ),
            },
        ),
        responses={200: openapi.Response("Сообщение доставлено")},
    )
    def post(self, request, *args, **kwargs):
        """
        Отправляет сообщение пользователю на обращение.
        """
        ticket_id = request.data.get("ticket_id")
        ticket = get_object_or_404(Tickets, id=ticket_id)
        if ticket.status == "closed":
            return Response(
                {"error": "Обращение закрыто"},
                status=status.HTTP_403_FORBIDDEN,
            )

        message = request.data.get("message")

        if not ticket_id or not message:
            return Response(
                {"error": "ticket_id и message обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_tasks_send_mail(
            ticket,
            subject=f"Re: {ticket.subject}",
            body=message,
        )
        return Response({"message": "Сообщение доставлено"}, status=status.HTTP_200_OK)
