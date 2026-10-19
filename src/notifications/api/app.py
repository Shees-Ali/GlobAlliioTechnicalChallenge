"""HTTP intake adapter. It decodes the request, calls the core and translates the outcome. It holds no rules."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from notifications.core.errors import DeliveryError, ErrorCode, InvalidEventError, InvalidPreferenceError
from notifications.core.preferences import PreferenceService
from notifications.core.service import NotificationService
from notifications.simulated.in_app_channel import InAppChannel
from notifications.simulated.in_memory_directory import InMemoryUserDirectory
from notifications.simulated.in_memory_preferences import InMemoryPreferenceStore
from notifications.simulated.in_memory_processed_events import InMemoryProcessedEvents
from notifications.simulated.sample_users import SAMPLE_USERS, UNREACHABLE_TOKENS


def _rejected(error: InvalidEventError | InvalidPreferenceError | DeliveryError, status: int = 422) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": error.code.value, "message": error.message})


async def _json_body(request: Request, error_type: type[Exception]) -> object:
    try:
        return await request.json()
    except ValueError:
        raise error_type(ErrorCode.MALFORMED_FIELD, "body is not valid JSON")


def create_app(service: NotificationService, preference_service: PreferenceService) -> FastAPI:
    app = FastAPI(title="Gaming notifications")

    @app.post("/events")
    async def submit_event(request: Request) -> JSONResponse:
        try:
            outcome = service.handle_event(await _json_body(request, InvalidEventError))
        except InvalidEventError as error:
            return _rejected(error)
        except DeliveryError as error:
            return _rejected(error, status=503)  # the channel is unavailable, a retry may succeed
        return JSONResponse(content={"status": outcome.value})

    @app.put("/preferences")
    async def change_preference(request: Request) -> JSONResponse:
        try:
            preference_service.change(await _json_body(request, InvalidPreferenceError))
        except InvalidPreferenceError as error:
            return _rejected(error)
        return JSONResponse(content={"status": "updated"})

    return app


def build_default_app() -> FastAPI:
    """Wire the simulated dependencies for `uvicorn notifications.api.app:app`."""
    directory = InMemoryUserDirectory(SAMPLE_USERS)
    preferences = InMemoryPreferenceStore()  # shared, so a change applies to the next event
    channel = InAppChannel(unreachable_tokens=UNREACHABLE_TOKENS)
    service = NotificationService(directory, channel, InMemoryProcessedEvents(), preferences)
    app = create_app(service, PreferenceService(directory, preferences))
    app.state.channel = channel  # lets tests and the demo see what each client would have received
    return app


app = build_default_app()
