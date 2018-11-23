# This is used when a new Role object is created for a user and Node
# 	to figure out which permissions to add to the Role's ManyToMany field
ROLES_MAP = {
	"team_member": [
		"read_team"
	],
	"team_lead": [
		"read_project",
		"update_project",
		"read_topic",
		"read_team",
		"update_team"
	],
	"team_admin": [
		"create_project",
		"read_project",
		"update_project",
		"delete_project",
		"add_team_member",
		"update_team_user_role",
		"remove_team_user",
		"read_team",
		"update_team",
		"delete_team",
		"read_topic",
		"add_project_viewer",
		"update_project_user_role"
	],

	"project_viewer": [
		"read_project",
		"read_topic"
	],
	"project_contributor": [
		"read_project",
		"update_project",
		"create_topic",
		"read_topic",
		"update_topic"
	],
	"project_admin": [
		"add_project_viewer",
		"update_project_user_role",
		"remove_project_user",
		"read_project",
		"update_project",
		"create_topic",
		"read_topic",
		"update_topic",
		"delete_topic",
		"add_topic_viewer",
		"update_topic_user_role",
		"remove_topic_user"
	],

	"topic_viewer": [
		"read_topic"
	],
	"topic_contributor": [
		"read_topic",
		"update_topic"
		"add_topic_viewer",
		"update_topic_user_role",
		"remove_topic_user"
	]
}