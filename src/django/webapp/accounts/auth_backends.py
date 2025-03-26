import jwt
from jwt.algorithms import RSAAlgorithm
import requests
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from .models import CognitoUser


COGNITO_POOL_ID = settings.COGNITO_USER_POOL_ID
COGNITO_REGION = settings.AWS_REGION_NAME

def get_cognito_public_keys():
    url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_POOL_ID}/.well-known/jwks.json"
    response = requests.get(url)
    return response.json()["keys"]

COGNITO_PUBLIC_KEYS = get_cognito_public_keys()

class CognitoJWTAuthentication(BaseBackend):
    def get_user(self, sub):
        print("Inside AuthBackends get_user()")
        try:
            return CognitoUser.objects.get(sub=sub)
        except CognitoUser.DoesNotExist:
            return None
    
    def authenticate(self, request, token=None):
        print("Inside AuthBackends authenticate()")
        
        # if request.path in ["/auth/sign-up/", "/auth/sign-in/"]:
        #     print(f"Skipping auth for {request.path}")
        #     return None
        
        token = request.headers.get("Authorization")
        print(f"got headers: {token}")
        print(" ")
        
        if token and token.startswith("Bearer "):
            token = token.replace("Bearer ", "").strip()
        
            try:
                print(f"Token Type: {type(token)}, Token Value: {token}")
                header = jwt.get_unverified_header(token)
                print(f"header: {header}")
                key = next(k for k in COGNITO_PUBLIC_KEYS if k["kid"] == header["kid"])
                public_key = RSAAlgorithm.from_jwk(key)
                print(f"public key: {public_key}")
                decoded_token = jwt.decode(
                    token,
                    public_key,
                    algorithms=["RS256"],
                    audience=settings.COGNITO_APP_CLIENT_ID,
                    issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_POOL_ID}",
                )

                # get user based on Cognito uuid
                sub = decoded_token.get("sub")
                user = CognitoUser.objects.get(sub=sub)
                print(f"Authenticated CognitoUser: {user.username}")
                print(user)
                return user

            except CognitoUser.DoesNotExist:
                print(f"No CognitoUser found for sub: {sub}")
                return None
            except Exception as e:
                print("JWT authentication error:", str(e))
                return None
            
        else:
            print("No token provided")
            return None