from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from . import models
import json


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        try:
            print(self.scope["user"], self.scope["headers"])
            self.node = models.TreeStructure.objects.get(_id=self.scope["url_route"]["kwargs"]["node_id"])
            # Setting the room name for the node - is created if doesn't already exist
            # Name is not allowed to have special characters, but this works since _id is alphanumeric
            self.chat_group_name = 'chat_%s' % str(self.node._id)
            # Joining the room if it exists, or creating a new one 
            # This actually makes a redis entry
            async_to_sync(self.channel_layer.group_add)(
                self.chat_group_name,
                self.channel_name
            )

            # Only accept the connection if node exists
            self.accept()
        except models.TreeStructure.DoesNotExist:
            self.close()


    def disconnect(self, close_code):
        # Leave room group during disconnect - removing socket from redis channel
        async_to_sync(self.channel_layer.group_discard)(
            self.chat_group_name,
            self.channel_name
        )

    def receive(self, text_data):
        """ Receives the message from websocket, sender and sent_time as input and creates the model entry """
        data = json.loads(text_data)

        async_to_sync(self.channel_layer.group_send)(
            self.chat_group_name,
            {
                'type': 'chat_message',
                'message': data
            }
        )

    # Receive message from chat group
    def chat_message(self, event):
        message = event['message']
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message
        }))