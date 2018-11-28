from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from rest_framework.response import Response
from vpmoprj.serializers import *

class AllUsersSerializer(serializers.ModelSerializer):
    _id = ObjectIdField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = (
            'email',
            'password',
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


# class UserUpdateSerializer(ModelSerializer):
#     # email = serializers.EmailField()
#     # fullname = serializers.CharField()
#     # username = serializers.CharField()
#     password = CharField(write_only=True)
#
#     def update(self, instance, validated_data):
#         instance.email = validated_data.get('email', instance.email),
#         instance.fullname = validated_data.get('fullname', instance.fullname),
#         instance.username = validated_data.get('username', instance.username),
#         instance.password = validated_data.get('password', instance.set_password(validated_data['password'])),
#         instance.save()
#         return instance
#
#     class Meta:
#         model = get_user_model()
#         fields = ('id', 'email', 'password', 'fullname', 'username')


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

        # fields = '__all__'

        # read_only_fields = ('created_at', 'updated_at',)

        # def create(self, validated_data):
        #     return MyUser.objects.create(**validated_data)
        #
        # def update(self, instance, validated_data):
        #     instance.username = validated_data.get('username', instance.username)
        #     instance.tagline = validated_data.get('tagline', instance.tagline)
        #
        #     instance.save()
        #
        #     password = validated_data.get('password', None)
        #     confirm_password = validated_data.get('confirm_password', None)
        #
        #     if password and confirm_password and password == confirm_password:
        #         instance.set_password(password)
        #         instance.save()
        #
        #     update_session_auth_hash(self.context.get('request'), instance)
        #
        #     return instance