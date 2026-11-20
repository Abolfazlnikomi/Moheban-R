from .models import Scope


def experience_access(request):
    if not hasattr(request, '_experience_access'):
        user = request.user
        request._experience_access = None
        if user.is_authenticated and user.is_active:
            if user.is_superuser:
                request._experience_access = Scope.objects.all()
            else:
                access = getattr(user, 'experience_access', None)
                if access is not None and access.enabled:
                    request._experience_access = access.scopes.all()
    return request._experience_access
