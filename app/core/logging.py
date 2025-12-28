import logging
import sys

from app.core.config.settings import settings


def setup_logging() -> None:
    """Configure application logging."""
    log_level = logging.DEBUG if settings.debug else logging.INFO
    log_format = (
        '{"time": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
        if settings.environment == "production"
        else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo else logging.WARNING
    )


# Initialize logging on module import
setup_logging()

# Create module-level logger
logger = logging.getLogger(__name__)
