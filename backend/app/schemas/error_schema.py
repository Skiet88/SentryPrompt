"""Error response bodies. Used both by the exception handlers and in the
OpenAPI docs, so the documented format is always the real one."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    message: str


class FieldProblem(BaseModel):
    field: str
    problem: str


class ValidationErrorResponse(ErrorResponse):
    """422: names the field and the problem; never echoes submitted values."""

    details: list[FieldProblem]


ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    400: {"model": ErrorResponse, "description": "Invalid input (e.g. whitespace-only prompt)"},
    413: {"model": ErrorResponse, "description": "Request body too large"},
    422: {
        "model": ValidationErrorResponse,
        "description": "Invalid request; submitted values are never echoed",
    },
    429: {"model": ErrorResponse, "description": "Rate limit reached; see the Retry-After header"},
    500: {"model": ErrorResponse, "description": "Server or configuration error (generic message)"},
}
