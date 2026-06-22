from django.contrib.auth.models import User
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(
        write_only = True
    )




class RegisterSerializer(serializers.ModelSerializer):
    class Meta :
        model = User
        fields = [
            "username",
            "email",
            "password"
        ]
        # extra_kwargs = {
        #     "password": {"write_only": True}
        # }
        password = serializers.CharField(
            write_only = True
        )
    
    def create(self,validated_data):
        # return User.objects.create_user(
        #     username=validated_data["username"],
        #     email=validated_data["email"],
        #     password=validated_data["password"]

        # )
        return User.objects.create_user(
            **validated_data
        )