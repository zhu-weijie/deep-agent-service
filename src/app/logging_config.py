import logging
from pythonjsonlogger import jsonlogger


def setup_logging():
    """
    Configures structured JSON logging for the application.
    """
    logger = logging.getLogger()
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a new handler that streams to console
    log_handler = logging.StreamHandler()

    # Use a custom formatter to output logs in JSON format
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s"
    )
    log_handler.setFormatter(formatter)

    # Add the new handler to the root logger
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)

    # Mute overly verbose third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
