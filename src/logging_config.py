"""
Shared logging configuration for the application.

This module provides consistent logging setup across all modules
(API, worker, tasks, etc.).
"""

import logging


def setup_logging(debug: bool = False) -> logging.Logger:
    """
    Configure application logging with consistent formatting.

    Args:
        debug: If True, sets log level to DEBUG; otherwise INFO

    Returns:
        Configured logger for the calling module
    """
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Get logger for the calling module
    # Note: When called from a module, __name__ will be the calling module's name
    return logging.getLogger(__name__)
