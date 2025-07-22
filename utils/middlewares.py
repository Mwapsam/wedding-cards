import json
import logging

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    MAX_BODY_LENGTH = 1024 * 4

    def process_request(self, request):
        if request.path.startswith(("/static/", "/media/")):
            return

        if logger.isEnabledFor(logging.INFO):
            logger.info("%s %s", request.method, request.get_full_path())

        if logger.isEnabledFor(logging.DEBUG):
            headers = {
                k: v
                for k, v in request.META.items()
                if k.startswith("HTTP_") and k != "HTTP_AUTHORIZATION"
            }
            logger.debug("Headers: %s", headers)

            if request.method in ("POST", "PUT", "PATCH"):
                content_type = request.META.get("CONTENT_TYPE", "")
                if content_type.startswith("application/json"):
                    self._log_json_body(request)

        return None

    def _log_json_body(self, request):
        """Log JSON request body only if within size limits and logging is enabled."""
        content_length = request.META.get("CONTENT_LENGTH")
        if not content_length:
            logger.debug("No Content-Length header, skipping JSON body logging.")
            return

        try:
            cl = int(content_length)
            if cl > self.MAX_BODY_LENGTH:
                logger.debug(
                    "Content-Length %s exceeds limit (%s), skipping JSON body logging.",
                    cl,
                    self.MAX_BODY_LENGTH,
                )
                return
        except ValueError:
            logger.debug("Invalid Content-Length value, skipping JSON body logging.")
            return

        try:
            body = request.body[: self.MAX_BODY_LENGTH].decode("utf-8")
            data = json.loads(body)
            logger.debug("JSON Body: %s", data)
        except UnicodeDecodeError:
            logger.debug("Failed to decode request body as UTF-8.")
        except json.JSONDecodeError:
            logger.debug("Failed to parse request body as JSON.")

    def process_response(self, request, response):
        if logger.isEnabledFor(logging.INFO):
            logger.info("Response status: %s", response.status_code)
        return response
