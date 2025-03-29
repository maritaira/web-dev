import boto3
from django.conf import settings


IDENTITY_POOL_ID = settings.COGNITO_IDENTITY_POOL_ID
USER_POOL_ID = settings.COGNITO_USER_POOL_ID
REGION_NAME = settings.AWS_REGION_NAME
APP_CLIENT_ID = settings.COGNITO_APP_CLIENT_ID

# Init Boto3 clients
cognito_identity_client = boto3.client('cognito-identity', region_name=REGION_NAME) 
cognito_idp_client = boto3.client('cognito-idp', region_name=REGION_NAME)

def get_cognito_identity_id(id_token):
    """
    Retrieves the Cognito Identity ID from the Identity Pool using the user's access token.
    """
    try:
        # Get Identity ID from Identity Pool
        response = cognito_identity_client.get_id(
            IdentityPoolId=IDENTITY_POOL_ID,
            Logins={
                f'cognito-idp.{REGION_NAME}.amazonaws.com/{USER_POOL_ID}': id_token
            }
        )
        identity_id = response['IdentityId']
        print(f"Cognito Identity ID: {identity_id}")
        return identity_id
    except Exception as e:
        print(f"Error getting Cognito Identity ID: str{e}")
        return None
    


def check_caller_identity(client):
    try:
        identity = client.get_caller_identity()
        print(f"UserID: {identity['UserId']}")
        print(f"AWS Account: {identity['Account']}")
        print(f"ARN: {identity['Arn']}")
    except Exception as e:
        print(f"Error getting caller identity: {e}")
        

def get_s3_client(identity_id, id_token):
    """
    Returns an S3 client with temporary credentials scoped to the Cognito Identity ID.
    """
    try:
        print(f"Retrieving temporary credentials for ID: {identity_id}")
        
        # Get temporary credentials
        response = cognito_identity_client.get_credentials_for_identity(
            IdentityId=identity_id,
            Logins={
                f'cognito-idp.{REGION_NAME}.amazonaws.com/{USER_POOL_ID}': id_token
            }
        )
        
        print(f"Response: {response}")
        
        credentials = response['Credentials']
        
        print("Initializing S3 client with temporary credentials")
        # Initialize the S3 client with temporary credentials
        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=REGION_NAME
        )
        print("Session created")
        
        print("Chekcing caller identity now")
        check_caller_identity(session.client('sts'))
        
        s3_client = session.client('s3')
        print('S3 client created sucessfully')
        
        
        return s3_client
    except Exception as e:
        print(f"Error getting S3 client: str{e}")
        return None    


def cognito_sign_up(username, password, email, name, lastname):
    """
    Returns Cognito IDP SignUp Response.
    """
    try:
        response = cognito_idp_client.sign_up(
            ClientId=APP_CLIENT_ID,
            Username=username,
            Password=password,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'name', 'Value': name},
                {'Name': 'custom:lastname', 'Value': lastname},
            ],
        )
        
        return response
    except cognito_idp_client.exceptions.UsernameExistsException as e:
        print(f"User {username} already exists")
        return e
    except Exception as e:
        print(f"Error Signing Up: str{e}")
        return None
    
def cognito_confirm_sign_up(username):
    """
    Returns Cognito IDP SignUp Confirmation Response.
    """
    try:
        confirm = cognito_idp_client.admin_confirm_sign_up(
            UserPoolId=USER_POOL_ID,
            Username=username
        )
        
        return confirm
    except Exception as e:
        print(f"Error Confirming SignUp: str{e}")
        return None
    
def cognito_add_user_to_group(username, group):
    """
    Adds user to group.
    """
    try:
        cognito_idp_client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=username,
            GroupName=group,
        )
    except Exception as e:
        print(f"Error adding user to {group}: {e}")
        
def cognito_initiate_auth(username, password):
    """
    Return Cognito InitiateAuth Response.
    """
    try:
        response = cognito_idp_client.initiate_auth(
            ClientId=APP_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": password,
            },
        )
        
        return response
    except cognito_idp_client.exceptions.NotAuthorizedException as e:
        print("NotAuthorizedException: Incorrect username or password")
        return e

    except cognito_idp_client.exceptions.UserNotFoundException as e:
        print("NotFoundException: User not found")
        return e
    except Exception as e:
        print(f"Error logging in as {username}")
        return None
