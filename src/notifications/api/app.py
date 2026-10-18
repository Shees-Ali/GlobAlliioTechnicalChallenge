"""HTTP intake adapter. It decodes the request, calls the core and translates the outcome. It holds no rules."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from notifications.core.errors import ErrorCode, InvalidEventError
from notifications.core.service import NotificationService
from notifications.simulated.console_delivery import ConsoleDelivery
from notifications.simulated.in_memory_directory import InMemoryUserDirectory
from notifications.simulated.in_memory_processed_events import InMemoryProcessedEvents
from notifications.simulated.sample_users import SAMPLE_USERS


def create_app(service: NotificationService) -> FastAPI:
    app = FastAPI(title="Gaming notifications")

    @app.post("/events")
    async def submit_event(request: Request) -> JSONResponse:
        try:
            try:
                payload = await request.json()
            except ValueError:
                raise InvalidEventError(ErrorCode.MALFORMED_FIELD, "body is not valid JSON")
            service.handle_event(payload)
        except InvalidEventError as error:
            return JSONResponse(
                status_code=422, content={"code": error.code.value, "message": error.message}
            )
        return JSONResponse(content={"status": "processed"})

    return app


def build_default_app() -> FastAPI:
    """Wire the simulated dependencies for `uvicorn notifications.api.app:app`."""
    service = NotificationService(
        InMemoryUserDirectory(SAMPLE_USERS), ConsoleDelivery(), InMemoryProcessedEvents()
    )
    return create_app(service)


app = build_default_app()
