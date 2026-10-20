"""HTTP intake adapter. It decodes the request, calls the core and translates the outcome. It holds no rules.

The event and preference routes are plain `def`, so FastAPI runs the synchronous core in its
thread pool and a slow delivery never blocks the event loop (FR-65). The demo's live feeds are
`async` because they stream on the loop (see api/demo.py).
"""

from typing import Any

from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from notifications.core.errors import (
    DeliveryError,
    ErrorCode,
    EventInProgressError,
    InvalidEventError,
    InvalidPreferenceError,
)
from notifications.core.preferences import PreferenceService
from notifications.core.service import NotificationService
from notifications.api.demo import demo_router
from notifications.simulated.sample_users import UNREACHABLE_TOKENS
from notifications.simulated.wiring import build_simulated


def _rejected(
    error: InvalidEventError | InvalidPreferenceError | DeliveryError | EventInProgressError, status: int = 422
) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": error.code.value, "message": error.message})


def _body_not_json(request: Request, error: RequestValidationError) -> JSONResponse:
    # FastAPI parses the body before a route runs. A body it cannot read gets our own error format.
    return JSONResponse(
        status_code=422, content={"code": ErrorCode.MALFORMED_FIELD.value, "message": "body is not valid JSON"}
    )


def create_app(service: NotificationService, preference_service: PreferenceService) -> FastAPI:
    app = FastAPI(title="Gaming notifications")
    app.add_exception_handler(RequestValidationError, _body_not_json)

    @app.post("/events")
    def submit_event(payload: Any = Body(...)) -> JSONResponse:
        try:
            outcome = service.handle_event(payload)
        except InvalidEventError as error:
            return _rejected(error)
        except DeliveryError as error:
            return _rejected(error, status=503)  # the channel is unavailable, a retry may succeed
        except EventInProgressError as error:
            return _rejected(error, status=409)  # another copy is still running, retry later
        return JSONResponse(content={"status": outcome.value})

    @app.put("/preferences")
    def change_preference(payload: Any = Body(...)) -> JSONResponse:
        try:
            preference_service.change(payload)
        except InvalidPreferenceError as error:
            return _rejected(error)
        return JSONResponse(content={"status": "updated"})

    return app


def build_default_app() -> FastAPI:
    """Wire the simulated dependencies for `uvicorn notifications.api.app:app`."""
    sim = build_simulated()
    app = create_app(sim.service, sim.preference_service)
    app.state.channel = sim.channel  # lets tests and the demo see what each client would have received
    app.include_router(demo_router(sim.channel, sim.users, UNREACHABLE_TOKENS, sim.preferences))
    return app


app = build_default_app()
