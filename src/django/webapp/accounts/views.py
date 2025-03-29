from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import SignInSerializer, SignUpSerializer
from .models import CognitoUser
from .cognito_utils import get_cognito_identity_id, cognito_sign_up, cognito_confirm_sign_up, cognito_add_user_to_group, cognito_initiate_auth
from django.views.decorators.csrf import csrf_exempt
import requests
import json
import base64


class SignUpView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # print("in SignUpView")
        req = request.data
        # print(req)
        # print(f"content type: {request.content_type}")
        serializer = SignUpSerializer(data=req)
        if serializer.is_valid():
            data = serializer.validated_data
            print(data)
            email = data["email"]
            name = data["name"]
            lastname = data["lastname"]
            username = data["username"]
            password = data["password"]
            
            try:
                # print("Running sign_up()")
                # create user in Cognito
                response = cognito_sign_up(username, password, email, name, lastname)
                print(response)
                
                sub = response.get("UserSub")
                print(f"sub: {sub}")
                
                # confirm the user (if auto-confirmation is disabled, they must verify via email)
                confirm = cognito_confirm_sign_up(username)     
                # print(confirm)
                
                 # Assign user to groups
                groups = []
                if "groups" in data:
                    for group in data["groups"]:
                        groups.append(group)
                        cognito_add_user_to_group(username, group)
                            
                print(f"Groups: {groups}")
                
                # Create the CognitoUser object in the database
                CognitoUser.objects.create(
                    username=username,
                    sub=sub,
                    email=email,
                    name=name,
                    lastname=lastname,
                    groups=groups
                )
                
                print(f"User {username} successfully registered as {groups}")
                return Response({"message": f"User successfully registered"})

            except Exception as e:
                print(str(e))
                return Response({"error": str(e)}, status=500)
            
        print(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            

class SignInView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        print("in SignInView")
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            print(data)
            username = data["username"]
            password = data["password"]
            
            try:
                # print("Running initiate_auth()")
                response = cognito_initiate_auth(username, password)
                # print(response)
                
                id_token = response["AuthenticationResult"]["IdToken"]
                access_token = response["AuthenticationResult"]["AccessToken"]
                refresh_token = response["AuthenticationResult"]["RefreshToken"]
                
                
                cognito_user = CognitoUser.objects.get(username=username)
                
                # Check if first-time login
                identity_id = get_cognito_identity_id(id_token)
                
                if identity_id:
                    cognito_user.cognito_identity_id = identity_id
                    cognito_user.save()
                    print(f"Assigned new Cognito Identity Id: {identity_id}")
                else:
                    print("Failed to fetch identity ID")
                
                response = Response({"message": "Sign-in successful",
                                 "id_token": id_token, 
                                 "access_token": access_token, 
                                 "refresh_token": refresh_token,
                                 "username": username,
                                 "cognito_identity_id": cognito_user.cognito_identity_id
                                 }, status=status.HTTP_200_OK,
                                    content_type="application/json")
                # print(f"Response data: {response.data}")
                # print("Content-Type Header:", response.headers.get('Content-Type')) 
                # print(f"response content_type: {type(response)}")
                return response
            except Exception as e:
                print(str(e))
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

''':
def getTokens(code):
    encodeData = base64.b64encode(bytes(f"{COGNITO_APP_CLIENT_ID}", "ISO-8859-1")).decode("ascii")
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {encodeData}'
    }
    
    body = {
        'grant_type': 'authorization_code',
        'client_id': COGNITO_APP_CLIENT_ID,
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    response = requests.post(TOKEN_ENDPOINT, data=body, headers=headers)
    
    id_token = response.json()['ide_token']
    decode_jwt.lambda_handler(id_token)
'''