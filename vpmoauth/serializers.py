from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import update_session_auth_hash
from rest_framework.response import Response


class AllUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            'email',
            'password',
            'fullname',
            'username',
            'id'
        )


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
                'id',
                'email',
                # 'password',
                'fullname',
                'username'
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
    email2 = serializers.EmailField(label='Confirm Email')
    password = serializers.CharField(write_only=True)

    class Meta:
        model = get_user_model()
        fields = ('email', 'email2', 'password', 'fullname', 'username')

    def validate_email2(self, value):
        data = self.get_initial()
        email1 = data.get('email')
        email2 = value
        if email1 != email2:
            raise serializers.ValidationError("Emails must match")
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