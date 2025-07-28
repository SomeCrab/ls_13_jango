from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from datetime import datetime, timezone
import jwt
import json
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """JWT authentication middleware handling token validation and rotation.

    Provides secure JWT-based authentication with automatic token refresh when:
    - Access tokens are about to expire
    - Refresh tokens are valid and rotate as needed
    
    Excludes specific paths from authentication requirements.
    Manages CSRF protection for non-GET requests using double token strategy."""
    EXCLUDED_PATHS = ['manager-login', 'manager-registration'] #, 'manager-logout']

    def process_request(self, request):
        """Authenticate request using JWT tokens.

        Args:
            request: Django HTTP request object

        Returns:
            None or HttpResponse if authentication fails

        Steps:
        1. Skip excluded paths
        2. Check access token validity and expiration
        3. Handle token refresh when needed
        4. Validate CSRF for non-GET requests
        5. Set authorization headers and meta variables"""
        match = resolve(request.path_info)
        if match.url_name in self.EXCLUDED_PATHS:
            return
        
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')
        
        # acces token flags
        need_refresh = False
        valid_access_token = None
        
        if access_token:
            try:
                token = AccessToken(access_token)
                valid_access_token = access_token
                
                if self._is_token_expiring_soon(token, settings.ACCES_TOKEN_THRESHOLD):
                    need_refresh = True
                    logger.debug("Access token expiring soon, will refresh")
                    
            except TokenError as e:
                logger.debug(f"Access token invalid: {e}")
                need_refresh = True
        else:
            # token in cookies
            need_refresh = True
        
        if need_refresh and refresh_token:
            try:
                refresh = RefreshToken(refresh_token)
                
                user_id = refresh.payload.get('user_id')
                if not user_id:
                    raise TokenError("No user_id in refresh token")
                
                try:
                    user = User.objects.get(pk=user_id)
                except User.DoesNotExist:
                    raise TokenError("User not found")
                
                new_access = refresh.access_token
                #print(f'new_access: {new_access}')
                rotation_flag = False
                if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', False) and self._is_token_expiring_soon(refresh, settings.REFRESH_TOKEN_THRESHOLD):
                    if settings.SIMPLE_JWT.get('BLACKLIST_AFTER_ROTATION', False):
                        try:
                            refresh.blacklist()
                        except AttributeError:
                            pass
                    
                    new_refresh = RefreshToken.for_user(user)
                    rotation_flag = True
                else:
                    # use old refresh
                    new_refresh = refresh
                
                csrf_token = self._generate_csrf_token()
                new_access['csrf'] = csrf_token
                #print(f'new_access csft: {new_access}')
                if rotation_flag:
                    request._new_tokens = {
                        'access': str(new_access),
                        'refresh': str(new_refresh),
                        'csrf': csrf_token
                    }
                else:
                    request._new_tokens = {
                        'access': str(new_access),
                        'csrf': csrf_token
                    }

                
                valid_access_token = str(new_access)
                logger.info(f"Successfully refreshed tokens for user {user.username}")
                
            except TokenError as e:
                # user must relog
                logger.warning(f"Refresh token invalid: {e}")
                request._auth_failed = True
                return
            except Exception as e:
                logger.error(f"Unexpected error during token refresh: {e}")
                request._auth_failed = True
                return
        
        # set meta
        if valid_access_token:
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {valid_access_token}'
            
            # CSRF for non GET requests
            if request.method not in ['GET', 'HEAD', 'OPTIONS']:
                self._validate_csrf(request, valid_access_token)
        elif not need_refresh:
            request._auth_failed = True
    
    def _is_token_expiring_soon(self, token, threshold):
        """ checks if token expiring in threshold time """
        try:
            exp_timestamp = token.payload.get('exp')
            if not exp_timestamp:
                return False
                
            exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            current_time = datetime.now(timezone.utc)
            time_until_expiry = (exp_time - current_time).total_seconds()
            
            return 0 < time_until_expiry < threshold
        except Exception as e:
            logger.error(f"Error checking token expiry: {e}")
            return False

    def _generate_csrf_token(self):
        import secrets
        return secrets.token_urlsafe(32)
    
    def _validate_csrf(self, request, access_token):
        """ validate CSRF for Double Token Strategy """
        try:
            payload = jwt.decode(
                access_token,
                settings.SECRET_KEY,
                algorithms=[settings.CSRF_TOKEN_ALGORITHM]
            )
            
            csrf_from_token = payload.get('csrf')
            csrf_from_header = request.headers.get('X-CSRF-Token')
            
            if not csrf_from_header or csrf_from_token != csrf_from_header:
                request._csrf_failed = True
                logger.warning("CSRF validation failed")
                
        except jwt.InvalidTokenError:
            request._csrf_failed = True
    
    def process_response(self, request, response):
        """Handle response after authentication processing.

        Args:
            request: Django HTTP request object
            response: Django HTTP response object

        Returns:
            Response with updated headers and cookies if new tokens were generated."""
        if hasattr(request, '_auth_failed'):
            response.status_code = 401
            response.content = json.dumps({
                'error': 'Authentication required',
                'code': 'authentication_failed'
            })
            response['Content-Type'] = 'application/json'
            
            response.delete_cookie('access_token', path='/')
            response.delete_cookie('refresh_token', path='/')
            return response
        
        if hasattr(request, '_csrf_failed'):
            response.status_code = 403
            response.content = json.dumps({
                'error': 'CSRF validation failed',
                'code': 'csrf_failed'
            })
            response['Content-Type'] = 'application/json'
            return response
        
        if hasattr(request, '_new_tokens'):
            tokens = request._new_tokens
            
            response.set_cookie(
                key='access_token',
                value=tokens['access'],
                max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
                httponly=True,
                secure=getattr(settings, 'SESSION_COOKIE_SECURE', False),
                samesite='Lax',
                path='/'
            )
            
            if 'refresh' in tokens:
                response.set_cookie(
                    key='refresh_token',
                    value=tokens['refresh'],
                    max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
                    httponly=True,
                    secure=getattr(settings, 'SESSION_COOKIE_SECURE', False),
                    samesite='Lax',
                    path='/'
                )
            
            if response.get('Content-Type', '').startswith('application/json'):
                try:
                    data = json.loads(response.content)
                    data['csrf_token'] = tokens['csrf']
                    response.content = json.dumps(data)
                except:
                    pass
            
            logger.debug("New tokens set in cookies")
        
        return response