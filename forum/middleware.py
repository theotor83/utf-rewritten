class ForceHTTPSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.META['HTTP_X_FORWARDED_PROTO'] = 'https'
        request._is_secure_override = True
        return self.get_response(request)
