# Setting up Django
import sys
sys.path.insert(0, 'C:\\Users\\WiggyAer\\djangopy27\\vpmo')
sys.path.insert(0, '/PATH/TO/VPMOAPP')

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'vpmoprj.settings'

import django
django.setup()

from vpmoapp.models import *
from guardian.shortcuts import assign_perm


def main(user, perm, team):
	""" Assigns given perm for given team to given user """
	permission = assign_perm(perm, user, team)
	print(perm, "For team", team.name, "Assigned to", user.email)


if __name__ == "__main__":
	import argparse
	parser = argparse.ArgumentParser(description='Give permissions to users')

	parser.add_argument("-u", type=str, help="User Email to add permission to")
	parser.add_argument("-p", type=str, help="Permission to add to user")
	parser.add_argument("-t", type=str, help="Name of Team to add permission for")

	args = parser.parse_args()

	user = MyUser.objects.get(email=args.u)
	team = Team.objects.get(name=args.t)
	perms = args.p
	assert perms in ["owned_obj", "contribute_obj", "read_obj"]

	main(user, perms, team)

	