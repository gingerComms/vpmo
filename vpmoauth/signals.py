from django.db.models.signals import pre_delete
from django.dispatch import receiver
from vpmoauth.models import MyUser


@receiver(pre_delete, sender=MyUser, dispatch_uid="myuser_delete_signal")
def delete_user_avatar(sender, instance, using, **kwargs):
	if instance.avatar:
		instance.avatar.delete()
