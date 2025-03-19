from jwt import algorithms
import requests
import jwt
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import authenticate, login
from webapp.settings import AWS_REGION_NAME, COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID

COGNITO_ISSUER = f"https://cognito-idp.{AWS_REGION_NAME}.amazonaws.com/{COGNITO_USER_POOL_ID}"
COGNITO_JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

class CognitoAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        token = request.headers.get("Authorization")
        if not token:
            request.user_id = None
            request.user_groups = []
            return
        
        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "")
                
        try:
            # fetch public keys from cognito
            jwks = requests.get(COGNITO_JWKS_URL).json()
            public_keys = {key["kid"]: algorithms.RSAAlgorithm.from_jwk(key) for key in jwks["keys"]}
            
            # decode token header to find key id (kid)
            headers = jwt.get_unverified_header(token)
            public_key = public_keys.get(headers["kid"])
            
            if public_key is None:
                raise jwt.InvalidTokenError("Invalid kid")
            
            # verify and decode token
            decoded_token = jwt.decode(
                token, public_key, algorithms=["RS256"],
                audience=COGNITO_APP_CLIENT_ID,
                issuer=COGNITO_ISSUER
                )
            
            request.user_id = decoded_token["sub"]  # Cognito User ID
            request.user_groups = decoded_token.get("cognito:groups", [])  # List of Cognito Groups

        except jwt.ExpiredSignatureError:
            request.user_id = None
            request.user_groups = []

        except Exception:
            request.user_id = None
            request.user_groups = []
