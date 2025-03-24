from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from .serializers import SignInSerializer, SignUpSerializer
from django.views.decorators.csrf import csrf_exempt
from webapp.settings import COGNITO_APP_CLIENT_ID, COGNITO_USER_POOL_ID, AWS_REGION_NAME, REDIRECT_URI, TOKEN_ENDPOINT
import requests
import boto3
import json
import base64


# initializing AWS Cognito client
client = boto3.client("cognito-idp", region_name=AWS_REGION_NAME)


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
                # print("in try block")
                # create user in Cognito
                response = client.sign_up(
                    ClientId=COGNITO_APP_CLIENT_ID,
                    Username=username,
                    Password=password,
                    UserAttributes=[
                        {
                            'Name': 'email',
                            'Value': email
                        },
                        {
                            'Name': 'name',
                            'Value': name
                        },
                        {
                            'Name': 'custom:lastname',
                            'Value': lastname
                        },
                    ],
                )
                
                print(response)
                
                # confirm the user (if auto-confirmation is disabled, they must verify via email)
                confirm = client.admin_confirm_sign_up(
                    UserPoolId=COGNITO_USER_POOL_ID,
                    Username=username
                )
                
                # print(confirm)
                
                 # Assign user to groups
                if "groups" in data:
                    for group in data["groups"]:
                        try:
                            client.admin_add_user_to_group(
                                UserPoolId=COGNITO_USER_POOL_ID,
                                Username=username,
                                GroupName=group,
                            )
                        except Exception as e:
                            print(f"Error adding user to {group}: {e}")
                
                print(f"User {username} successfully registered")
                return Response({"message": f"User successfully registered"})
            
            except client.exceptions.UsernameExistsException:
                return Response({"error": "User already exists"}, status=400)

            except Exception as e:
                print(str(e))
                return Response({"error": str(e)}, status=500)
            
        print(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            

class SignInView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            print(data)
            username = data["username"]
            password = data["password"]
            
            try:
                response = client.initiate_auth(
                    ClientId=COGNITO_APP_CLIENT_ID,
                    AuthFlow="USER_PASSWORD_AUTH",
                    AuthParameters={
                        "USERNAME": username,
                        "PASSWORD": password,
                    },
                )
                
                id_token = response["AuthenticationResult"]["IdToken"]
                access_token = response["AuthenticationResult"]["AccessToken"]
                
                # Get user groups
                user_info = client.get_user(AccessToken=access_token)
                groups = []
                for attr in user_info["UserAttributes"]:
                    if attr["Name"] == "cognito:groups":
                        groups = attr["Value"].split(",")  # Store groups in a list
                print(f"Successfully signed in as {user_info["Username"]}")
                return Response({"id_token": id_token, "access_token": access_token, "groups": groups}, status=status.HTTP_200_OK)
            except client.exceptions.NotAuthorizedException:
                print("notauthorizedexception")
                return Response({"error": "Incorrect username or password"}, status=status.HTTP_401_UNAUTHORIZED)

            except client.exceptions.UserNotFoundException:
                print("notfoundexception")
                return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)

            except Exception as e:
                print(str(e))
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

'''
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