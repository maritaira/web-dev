from jwt import algorithms
import requests
from jwt.algorithms import RSAAlgorithm
from django.http import JsonResponse
from cryptography.hazmat.primitives import serialization
from accounts.models import CognitoUser
from webapp.settings import AWS_REGION_NAME, COGNITO_USER_POOL_ID, COGNITO_APP_CLIENT_ID

COGNITO_ISSUER = f"https://cognito-idp.{AWS_REGION_NAME}.amazonaws.com/{COGNITO_USER_POOL_ID}"
COGNITO_JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"


def get_cognito_user(request):
    token = request.headers.get("Authorization", "").split("Bearer ")[-1]
    if not token:
        print("No token found")
        return None
    try:
        jwks = requests.get(COGNITO_JWKS_URL).json()
        public_keys = {key["kid"]: RSAAlgorithm.from_jwk(key) for key in jwks["keys"]}
        
        headers = jwt.get_unverified_header(token)
        print(f"JWT header: {headers}")
        public_key = public_keys.get(headers["kid"])
        print(f"public key: {public_key}")
        # pem = public_key.public_bytes(
        #     encoding=serialization.Encoding.PEM,
        #     format=serialization.PublicFormat.SubjectPublicKeyInfo
        # )
        # public_key = pem.decode('utf-8')
        # print(f"pem public key: {public_key}")
        
        decoded_token = jwt.decode(
            token, public_key, algorithms=["RS256"],
            audience=COGNITO_APP_CLIENT_ID,
            issuer=COGNITO_ISSUER
        )
        print(f"got decoded token")
        print(f"DECODED token: {decoded_token}")
        sub = decoded_token.get("sub")
        
        user = CognitoUser.objects.get(sub=sub)

        return user
    
    except CognitoUser.DoesNotExist:
        print("User not found in database")
        return JsonResponse({"error": "User not found"})
    except Exception as e:
        print(f"Token decode error: {str(e)}")
        return JsonResponse({"error": "decode error"})
    except jwt.ExpiredSignatureError:
        print("expired signature")
        return JsonResponse({'error': 'Token expired'}, status=401)
    except jwt.InvalidAudienceError:
        print("invalid audience")
        return JsonResponse({'error': 'Invalid audience'}, status=401)
    except jwt.InvalidIssuerError:
        print("invalid issuer")
        return JsonResponse({'error': 'Invalid issuer'}, status=401)
    except jwt.InvalidSignatureError:
        print("invalid signature")
        return JsonResponse({'error': 'Invalid signature'}, status=401)
    except jwt.InvalidKeyError:
        print("invalid key")
        return JsonResponse({'error': 'Invalid key'}, status=401)
    except jwt.InvalidAlgorithmError:
        print("invalid algorithm")
        return JsonResponse({'error': 'Invalid algorithm'}, status=401)
    except jwt.InvalidTokenError:
        print("invalid token")
        return JsonResponse({'error': 'Invalid token'}, status=401)

class CognitoAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        print("in call (middleware)")
        
        if request.path in ["/auth/sign-up/", "/auth/sign-in/"]:
            print(f"Skipping middleware for {request.path}")
            return self.get_response(request)
        
        request.user = get_cognito_user(request)

        print(f"Request Path: {request.path}, Method: {request.method}")
        print(request.user)
        print(request)
        try:
            response = self.get_response(request)
        except Exception as e:
            print(f"exception: {str(e)}")
        print(f"Response status: {response.status_code}")
        print(f"response: {response}")    
        return response
    