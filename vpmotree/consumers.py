from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync

from . import models
import json
from rest_framework_jwt.serializers import VerifyJSONWebTokenSerializer

from datetime import datetime as dt


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        try:
            jwt_token = {"token": self.scope["query_string"]}
            token_data = VerifyJSONWebTokenSerializer().validate(jwt_token)
            self.user = token_data["user"]

            self.node_id = str(models.TreeStructure.objects.get(_id=self.scope["url_route"]["kwargs"]["node_id"])._id)
            # Setting the room name for the node - is created if doesn't already exist
            # Name is not allowed to have special characters, but this works since _id is alphanumeric
            self.chat_group_name = 'chat_%s' % str(self.node_id)
            # Joining the room if it exists, or creating a new one 
            # This actually makes a redis entry
            async_to_sync(self.channel_layer.group_add)(
                self.chat_group_name,
                self.channel_name
            )

            # Only accept the connection if node exists
            self.accept()
        except:
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
        data["author"] = self.user.username

        node = models.TreeStructure.objects.get(_id=self.node_id)
        message = models.Message(content=data["content"], author=self.user, node=node,
            sent_on=dt.strptime(data["sent_on"], '%Y-%m-%dT%H:%M:%S.%fZ'))
        message.save()
        data["_id"] = str(message._id)

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