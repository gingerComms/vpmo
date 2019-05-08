
# Setting up Django

def create_base_permissions():
	from vpmoauth.models import UserRolePermission
	from vpmoauth.role_permissions_map import ROLES_MAP
	""" Creates the base permissions required for the roles implementation """
	perms = set([item for sublist in ROLES_MAP.values() for item in sublist])

	existing = list(UserRolePermission.objects.filter(name__in=perms).values_list('name', flat=True))

	to_create = [i for i in perms if i not in existing]

	models = []
	for perm in to_create:
		models.append(UserRolePermission(name=perm))

	created = UserRolePermission.objects.bulk_create(models)

	return created


if __name__ == "__main__":
	import sys
	import os
	import django

	sys.path.insert(0, 'C:\\Users\\WiggyAer\\djangopy27\\vpmo')
	sys.path.insert(0, 'G:\\Web\\vpmo_pc')
	os.environ['DJANGO_SETTINGS_MODULE'] = 'vpmoprj.prod_settings'
	django.setup()

	print(create_base_permissions())
