from rest_framework import serializers

class SignUpSerializer(serializers.Serializer):
    name = serializers.CharField()
    lastname = serializers.CharField()
    username = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    groups = serializers.ListField(child=serializers.CharField(), required=False)

class SignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)