from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        
        response = await call_next(request)
        
        if request.url.path.startswith("/api/"): # so that it apply to API routes, as CSP header will not allow API docs for instances /scalar or /docs...etc
            # Define headers similar to Helmet's defaults
            headers = {
                # This header enforces HTTPS by instructing the browser to automatically convert all HTTP requests to HTTPS for the specified duration. 
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                # Prevents browsers from MIME-sniffing content types, which could lead to security risks like executing a malicious script disguised as an image. 
                "X-Content-Type-Options": "nosniff",
                # Protects against clickjacking by controlling whether your page can be embedded in <frame>, <iframe>, or <object>. 
                # "X-Frame-Options": "DENY", # replaced with CSP frame-ancestors
                # Most modern browsers (Chrome, Firefox, Safari) have removed this feature due to reliability issues and potential abuse by attackers.
                # Set to 0 to explicitly disable it and rely on stronger protections like CSP. 
                "X-XSS-Protection": "0",
                # Controls access to cross-domain policy files, mainly used by Adobe Flash and PDF plugins. Set to none is the safest option
                "X-Permitted-Cross-Domain-Policies": "none", # none, master-only, by-content-type, all
                # Useful for privacy-sensitive sites to prevent leakage of user browsing behavior via DNS queries.
            	"X-DNS-Prefetch-Control": "off", # Acceptable if performance impact is acceptable
                # Controls how much referrer information is sent when navigating from your site to another.
                # We use strict-origin-when-cross-origin for a balanced approach — sends full URL for same-origin, only origin for HTTPS cross-origin, nothing on downgrade
                "Referrer-Policy": "strict-origin-when-cross-origin",
                # Isolates your browsing context from cross-origin windows. 
                "Cross-Origin-Opener-Policy": "same-origin", #  Use with Cross-Origin-Embedder-Policy for full site isolation. 
                # Requires all embedded resources (scripts, images, etc.) to be loaded with CORS or same-origin policies. 
                "Cross-Origin-Embedder-Policy": "require-corp",
                # CSP defines which sources of content are allowed to load
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
            }
            
            # Update response headers
            response.headers.update(headers)

        return response


