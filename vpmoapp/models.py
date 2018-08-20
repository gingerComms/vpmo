# mongodb+srv://alifradn:mdEla45Jig!@cluster0-srrwy.mongodb.net/test
#
# connect(
#     'mongodb://alifradn:mdEla45Jig!@cluster0-shard-00-00-6qb6a.mongodb.net:27017,cluster0-shard-00-01-6qb6a.mongodb.net:27017,cluster0-shard-00-02-6qb6a.mongodb.net:27017/test?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin',
#     alias='my-atlas-app'
# )
from __future__ import unicode_literals
# from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.template.defaultfilters import slugify
from guardian import shortcuts

from djongo import models
from django import forms

from vpmoauth.models import MyUser

from django.core.mail import send_mail
import guardian.mixins

# to add a field to mongodb collection after adding it to model
# 1- connect to mongodb via shell
# 2- use cluster0
# 3- db.[collection name].update({},{$set : {"field_name":null}},false,true)




class Comment(models.Model):
    content = models.TextField(blank=True, null=True)

    # def sample_view(self):
    #     current_user = self.user
    #     return current_user

    # author = sample_view()

    # author = models.ForeignKey(
    #     AUTH_USER_MODEL,
    #     on_delete=models.CASCADE,
    # )
    def __str__(self):
        return '%s' % (self.content)

    class Meta:
        abstract = True


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = (
            'content',
        )


class TreeStructure(models.Model):
    """ An implementation of Model Tree Structures with Materialized Paths in Django """
    path = models.CharField(null=False, max_length=4048)

    def get_element_path(self, elem=None):
        if elem is None:
            elem = self
        return str(elem._id)+"-{}".format(type(elem).__name__)

    def save(self, *args, **kwargs):
        # NOTE - Limit of recursion from MongoDB is 20! Do not create inheritances that exceed 20 levels!
        # If instance is a Team, just make sure the path is top level
        if isinstance(self, Team):
            self.path = ","+self.get_element_path()+","

            """ Commented to try single model based approach
            # We set all children paths in the Team save, because we might not be able to guarantee the order otherwise
            # Getting top level projects
            projects = Project.objects.filter(team___id=self._id)

            sub_projects = []

            # Iterate over children projects until no more children are found
            while len(projects):
                for project in projects:
                    # If project has a team parent, extend that path, otherwise use the project parent
                    if project.team is not None:
                        project.path = project.team.path + "{},".format(self.get_element_path(elem=project))
                    elif project.parent_project is not None:
                        project.path = project.parent_project.path + "{},".format(self.get_element_path(elem=project))
                    project.save()
                # Projects for the next loop
                projects = Project.objects.filter(parent_project__in=projects)
            """
        # If instance is a Project, set the path to parent's path + project_path
        elif isinstance(self, Project):
            if self.team is not None:
                self.path = self.team.path + "{},".format(self.get_element_path())
            elif self.parent_project is not None:
                self.path = self.parent_project.path + "{},".format(self.get_element_path())
        # Otherwise, just set path to parent project's path + current elem
        else:
            self.path = self.project.path + "{},".format(self.get_element_path())

        super(TreeStructure, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class Team(TreeStructure):
    _id = models.ObjectIdField()

    name = models.CharField(max_length=50)
    # owner = models.ReferenceField(User)
    user_linked = models.BooleanField(default=False)
    userTeam = models.CharField(max_length=151, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (
            ('created_obj', 'Admin Level Permissions',),
            ('contribute_obj', "Contributor Level Permissions",),
            ('read_obj', 'Read Level Permissions')
        )

    def __str__(self):
        return '%s' % (self.userTeam)


class Project(TreeStructure):
    _id = models.ObjectIdField()

    projectname = models.CharField(max_length=50, verbose_name="Project Name", default="Project Name - Default")
    description = models.TextField(blank=True, null=True)
    # comments = models.ArrayModelField(
    #     model_container=Comment,
    #     model_form_class=CommentForm,
    #     null=True
    # )
    start = models.DateField(null=True)
    owner = models.ForeignKey(MyUser, on_delete=models.CASCADE, null=True)

    # Many to One to both Teams and other Projects; one will always be null
    team = models.ForeignKey(Team, null=True, on_delete=models.CASCADE)
    parent_project = models.ForeignKey("self", null=True, on_delete=models.CASCADE)

    # organisation = models.ReferenceField(Organisation)
    # owner = models.ReferenceField(User)

    def __str__(self):
        return '%s' % (self.projectname)

    class Meta:
        ordering = ('projectname',)
        # objects = models.DjongoManager()


class Topic(TreeStructure):
    class Meta:
        abstract = True


# @receiver(pre_save, sender=Team)
# def my_callback(sender, instance, username, *args, **kwargs):
#     instance._id = slugify(instance.name) + '@' + username


def create_user_team(sender, instance, created, **kwargs):
    if created:
        # create a team Linked to the user
        team = Team.objects.create(
                name=instance.username + "'s team",
                userTeam="team@" + instance.username,
                user_linked=True
            )
        # User authentication

        # give the user created_obj permission against this team
        shortcuts.assign_perm("created_obj", instance, team)
        # consider not to give any other user created_obj permission against this team

        print('user-team was created')


post_save.connect(create_user_team, sender=MyUser)
