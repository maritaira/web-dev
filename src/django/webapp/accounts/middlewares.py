import jwt
import requests
from jwt.algorithms import RSAAlgorithm
# from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
# from django.contrib.auth import authenticate, login
from webapp.settings import AWS_REGION_NAME, COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID

COGNITO_ISSUER = f"https://cognito-idp.{AWS_REGION_NAME}.amazonaws.com/{COGNITO_USER_POOL_ID}"
COGNITO_JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

class CognitoAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        token = request.headers.get("Authorization")
        
        if token and token.startswith("Bearer "):
            token = token.replace("Bearer ", "").strip()
            
            print(f"Middlewares: Token Type: {type(token)}, Token Value: {token}")
            
            try:
                jwks = requests.get(COGNITO_JWKS_URL).json()
                public_keys = {key["kid"]: RSAAlgorithm.from_jwk(key) for key in jwks["keys"]}
                
                headers = jwt.get_unverified_header(token)
                public_key = public_keys.get(headers["kid"])

                if public_key:
                    decoded_token = jwt.decode(
                        token, public_key, algorithms=["RS256"],
                        audience=COGNITO_APP_CLIENT_ID,
                        issuer=COGNITO_ISSUER
                    )
                    request.user_id = decoded_token["sub"]
                    request.user_groups = decoded_token.get("cognito:groups", [])

            except jwt.ExpiredSignatureError:
                return JsonResponse({'error': 'Token expired'}, status=401)
            except jwt.InvalidTokenError:
                return JsonResponse({'error': 'Invalid token'}, status=401)
        return self.get_response(request)
    
    '''
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
            public_keys = {key["kid"]: RSAAlgorithm.from_jwk(key) for key in jwks["keys"]}
            
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
    '''