from channels.generic.websocket import WebsocketConsumer
from . import models
import json


class ChatConsumer(WebsocketConsumer):
	def connect(self):
		print("CONNECTING...")
		try:
			self.node = models.TreeStructure.objects.get(_id=self.scope["url_route"]["kwargs"]["node_id"])
			self.chatroom = models.Chatroom.objects.get(node=node)
			# Only accept the connection if node exists
			self.accept()
			print("Accepted")
		except TreeStructure.DoesNotExist:
			print("Rejected")
			self.close()


	def disconnect(self, close_code):
		pass

	def receive(self, data):
		""" Receives the message, sender and sent_time as input and creates the model entry """
		data = json.loads(data)
		print(data)

		self.send(text_data=json.dumps(data))