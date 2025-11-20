from django.contrib.auth.backends import BaseBackend
from users.models import Usuario

class EmailOrUsernameBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        try:
            # Always try to find user by email since that's our USERNAME_FIELD
            user = Usuario.objects.get(email_usuario=username)
        except Usuario.DoesNotExist:
            return None
        
        if user.check_password(password) and user.is_active:
            return user
        return None
    
    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None