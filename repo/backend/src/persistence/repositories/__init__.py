"""Thin persistence repositories. Routers/services import from here, never
from the model modules directly, to keep ORM details out of the call sites."""

from .attendance_repo import AttendanceRepository  # noqa: F401
from .auth_repo import AuthRepository  # noqa: F401
from .candidate_repo import CandidateRepository  # noqa: F401
from .document_repo import DocumentRepository  # noqa: F401
from .idempotency_repo import IdempotencyRepository  # noqa: F401
from .config_repo import ConfigRepository  # noqa: F401
from .order_repo import OrderRepository  # noqa: F401
