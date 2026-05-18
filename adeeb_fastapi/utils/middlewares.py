from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        
        response = await call_next(request)
        
        if request.url.path.startswith("/api/"): # so that it apply to API routes, as CSP header will not allow API docs for instances /scalar or /docs...etc
            # Define headers similar to Helmet's defaults
            headers = {
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Cross-Origin-Opener-Policy": "same-origin",
                "Cross-Origin-Embedder-Policy": "require-corp",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self';"
            }
            
            # Update response headers
            response.headers.update(headers)

        return response


