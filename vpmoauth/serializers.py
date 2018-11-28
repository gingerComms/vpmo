from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from rest_framework.response import Response
from vpmoprj.serializers import *
from vpmoauth.models import UserRole

class AllUsersSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'email',
            'fullname',
            'username',
            '_id',
            "avatar",
        )


class UserDetailsSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)
    favorite_nodes = MinimalNodeSerializer(required=False, many=True)

    class Meta:
        model = get_user_model()
        fields = (
                '_id',
                'email',
                # 'password',
                'fullname',
                'username',
                "favorite_nodes",
                "avatar",
        )


class UserDeserializer(serializers.ModelSerializer):
    email2 = serializers.EmailField(label='Confirm Email', source="get_email2")
    password = serializers.CharField(write_only=True)
    avatar = serializers.ImageField(max_length=100, required=False)

    class Meta:
        model = get_user_model()
        fields = ('email', 'email2', 'password', 'fullname', 'username', 'avatar')
        read_only_fields = ("email2",)

    def validate_email(self, value):
        """ Validates email from email2 """
        data = self.get_initial()
        email1 = data["email"]
        email2 = data.get("email2", None)
        if email1 != email2:
            raise serializers.ValidationError("Email And Email2 must match")
        return value

    def create(self, validated_data):
        user = get_user_model().objects.create_user(
            email=validated_data['email'],
            fullname=validated_data['fullname'],
            username=validated_data['username']
        )
        user.set_password(validated_data['password'])
        user.is_active = True
        user.save()
        return user