from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str

    # Security
    secret_key: str
    kek_path: str = "/secrets/kek"
    kek_current_version: str = "v1"
    tls_cert_path: str = "/certs/cert.pem"
    tls_key_path: str = "/certs/key.pem"

    # JWT
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    jwt_algorithm: str = "RS256"
    jwt_private_key_path: str = "/secrets/jwt_private.pem"
    jwt_public_key_path: str = "/secrets/jwt_public.pem"
    jwt_key_id: str = "mt-signing-1"
    jwt_issuer: str = "merittrack"
    jwt_audience: str = "merittrack-app"

    # Login throttle
    login_throttle_max_attempts: int = 5
    login_throttle_window_minutes: int = 15
    login_lockout_minutes: int = 15

    # Request signing — informational list used by frontend's SIGNED_PATHS;
    # backend enforcement is per-route via Depends(require_signed_request).
    # NOTE: /api/v1/auth/device/activate is NOT in this list. Activation uses a
    # challenge-signature payload (the device signs the enrollment nonce returned
    # by /device/challenge before any device_id exists), which is a distinct
    # bootstrap mechanism from canonical signed-request headers.
    signature_required_paths: list[str] = [
        "/api/v1/auth/password/change",
        "/api/v1/auth/device/{device_id}/rotate",
        "/api/v1/candidates/{candidate_id}/documents/upload",
        "/api/v1/orders",
        "/api/v1/orders/{order_id}/bargaining/offer",
        "/api/v1/orders/{order_id}/payment/proof",
        "/api/v1/orders/{order_id}/payment/confirm",
        "/api/v1/orders/{order_id}/voucher",
        "/api/v1/orders/{order_id}/milestones",
        "/api/v1/orders/{order_id}/refund",
        "/api/v1/orders/{order_id}/refund/process",
        "/api/v1/orders/{order_id}/after-sales",
        "/api/v1/orders/{order_id}/after-sales/{request_id}/resolve",
        "/api/v1/attendance/exceptions",
        "/api/v1/attendance/exceptions/{exception_id}/proof",
        "/api/v1/attendance/exceptions/{exception_id}/review",
    ]
    webcrypto_fallback_enabled: bool = False

    # Cache-stats worker — primary pipeline reads local access-log files;
    # heuristic metric-registry derivation is used only if logs unreadable/absent.
    cache_stats_log_backed: bool = True

    # Idempotency
    idempotency_key_ttl_hours: int = 24

    # Storage paths
    storage_root: str = "/data/uploads"
    exports_root: str = "/data/exports"
    access_log_root: str = "/data/access-logs"
    forecasts_root: str = "/data/forecasts"

    # Frontend
    frontend_dist_path: str = "/app/frontend_dist"

    # Application
    environment: str = "production"

    # Business rules (can be overridden by feature flags at runtime)
    auto_cancel_minutes: int = 30
    bargaining_window_hours: int = 48
    max_bargaining_offers: int = 3
    after_sales_window_days: int = 14
    nonce_window_seconds: int = 300
    clock_skew_tolerance_seconds: int = 30

    # File upload limits
    max_upload_size_bytes: int = 25 * 1024 * 1024  # 25 MB
    allowed_mime_types: list[str] = ["application/pdf", "image/jpeg", "image/png"]

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        if v not in ("development", "production"):
            raise ValueError("environment must be 'development' or 'production'")
        return v

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("secret_key must be at least 32 characters")
        return v


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
