from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from vpmoauth.models import MyUser
from vpmotree.models import Team


@receiver(pre_delete, sender=MyUser, dispatch_uid="myuser_delete_signal")
def delete_user_signal(sender, instance, using, **kwargs):
	if instance.avatar:
		instance.avatar.delete()
	if instance.twilio_sid:
		instance.delete_twilio_user()

@receiver(post_save, sender=MyUser, dispatch_uid="user_create_signal")
def create_user_signal(sender, instance, *args, **kwargs):
	# We're doing this in the post save so that we're sure the user has the _id attribute
	# Doing this in the save method means that we can't use the user's _id in twilio
	if not instance.twilio_sid:
		instance.create_twilio_user()
		instance.create_user_team()
		instance.save()
	else:
		# If twilio_sid exists, it means this is an update save
		instance.update_twilio_user()