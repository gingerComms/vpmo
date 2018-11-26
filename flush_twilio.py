from django.conf import settings
from twilio.rest import Client

# Need to do a django setup here

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

channels = client.chat.services(settings.TWILIO_CHAT_SERVICE_SID) \
                      .channels \
                      .list()

for channel in channels:
    client.chat.services(settings.TWILIO_CHAT_SERVICE_SID) \
           .channels(channel.sid) \
           .delete()


users = client.chat.services(settings.TWILIO_CHAT_SERVICE_SID).users.list()


for user in users:
    client.chat.services(settings.TWILIO_CHAT_SERVICE_SID) \
           .users(user.sid) \
           .delete()

