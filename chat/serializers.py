from rest_framework import serializers
from .models import ChatRoom, Message

class ChatRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatRoom
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    chat_room = serializers.StringRelatedField()

    class Meta:
        model = Message
        fields = '__all__'

