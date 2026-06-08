from apps.tenants.utils import set_current_tenant, clear_current_tenant


class TenantIsolationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response


    def __call__(self, request):
        if request.user and request.user.is_authenticated:
            if request.user.tenant:
                set_current_tenant(request.user.tenant)
        else:
            clear_current_tenant()
        try:
            response = self.get_response(request)
        finally:
            clear_current_tenant()
        return response
        