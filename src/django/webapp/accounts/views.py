from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from webapp.settings import COGNITO_APP_CLIENT_ID, COGNITO_USER_POOL_ID, AWS_REGION_NAME
import requests
import boto3
import json

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({"message": f"Hello, {request.user.username}"})

client = boto3.client("cognito-idp", region_name=AWS_REGION_NAME)

@csrf_exempt
def sign_up(request):
    if request.method == "POST":
        # get user details
        data = json.loads(request.body)
        print(data)
        email = data.get("email")
        name = data.get("name")
        lastname = data.get("lastname")
        username = data.get("username")
        password = data.get("password")
        user_group = data.get("user_group")
        
        if not email or not name or not lastname or not username or not password or not user_group:
            return Response({"error": "Missing required fields"}, status=400)
        
        print(f"name: {name}")
        
        try:
            print("in try block")
            # create user in Cognito
            print(f"Cognito client id: {COGNITO_APP_CLIENT_ID}")
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
            
            # Confirm the user (if auto-confirmation is disabled, they must verify via email)
            client.admin_confirm_sign_up(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=username
            )

            # Add the user to the specified group
            client.admin_add_user_to_group(
                UserPoolId=COGNITO_USER_POOL_ID,
                Username=username,
                GroupName=user_group
            )
            
            print(f"User {username} successfully registered as {user_group}")
            return Response({"message": f"User successfully registered as {user_group}"})
        
        except client.exceptions.UsernameExistsException:
            return Response({"error": "User already exists"}, status=400)

        except Exception as e:
            print(str(e))
            return Response({"error": str(e)}, status=500)
        
    print("Error, invalid request")
    return Response({"error": "Invalid request"}, status=400)
    
    
@csrf_exempt   
def sign_in(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print(data)
        username = data.get("username")
        password = data.get("password")
        
        if not username or not password:
            return Response({"error": "Missing username or password"}, status=400)
        
        try:
            response = client.initiate_auth(
                ClientId=COGNITO_APP_CLIENT_ID,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": username,
                    "PASSWORD": password,
                },
            )
            
            print(f"Successfully signed-in as {username}")
            return Response({
                "access_token": response["AuthenticationResult"]["AccessToken"],
                "id_token": response["AuthenticationResult"]["IdToken"],
                "refresh_token": response["AuthenticationResult"]["RefreshToken"],
            })
            
        except client.exceptions.NotAuthorizedException:
            return Response({"error": "Incorrect username or password"}, status=401)

        except client.exceptions.UserNotFoundException:
            return Response({"error": "User does not exist"}, status=404)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
        
    return Response({"error": "Invalid request"}, status=400)
        