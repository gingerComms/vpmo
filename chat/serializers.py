from rest_framework import serializers


class ChannelSerializer(serializers.Serializer):
	channel_sid = serializers.CharField()
	# If this is none, it means no messages have been read so far
	unread_messages_count = serializers.IntegerField()
