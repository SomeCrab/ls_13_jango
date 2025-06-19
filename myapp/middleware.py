# myapp/middleware.py
class MyCustomMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        # Код, выполняемый до обработки запроса
        response = self.get_response(request)
        # Код, выполняемый после обработки запроса
        return response