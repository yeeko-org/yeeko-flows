class LocalhostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if 'localhost' in request.META.get('HTTP_HOST', ''):
            request.META['HTTP_X_FORWARDED_HOST'] = 'localhost'
        return self.get_response(request)
