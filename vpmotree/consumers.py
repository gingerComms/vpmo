from channels.generic.websocket import WebsocketConsumer
import json


class ChatConsumer(WebsocketConsumer):
	def connect(self):
		print("CONNECTING...")
		self.accept()


	def disconnect(self, close_code):
		pass

	def receive(self, data):
		""" Receives the message, sender and sent_time as input and creates the model entry """
		data = json.loads(data)
		print(data)

		self.send(data=json.dumps(data))