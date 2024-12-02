from rest_framework import serializers
from .models import Tickets


class TicketsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tickets
        fields = "__all__"