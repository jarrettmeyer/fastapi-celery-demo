"""Calculation task implementation - performs mathematical operations on numbers."""

import logging
from pydantic import BaseModel, Field

from ..worker import celery_app

logger: logging.Logger = logging.getLogger(__name__)


class CreateCalculationTaskRequest(BaseModel):
    """Request model for creating a calculation task."""

    numbers: list[int] = Field(
        ..., min_length=1, max_length=100, description="List of integers to calculate"
    )
    operation: str = Field(
        ...,
        pattern="^(sum|product|average)$",
        description="Operation to perform: sum, product, or average",
    )


@celery_app.task(name="calculation_task", bind=True)
def calculation_task(self, numbers: list[int], operation: str) -> dict[str, object]:
    """
    Performs mathematical calculations on a list of numbers.

    Args:
        numbers: List of integers to calculate
        operation: Operation to perform ('sum', 'product', or 'average')

    Returns:
        dict with operation, result, and count of numbers
    """
    logger.info(
        f"Task {self.request.id} starting: {operation} on {len(numbers)} numbers"
    )

    result: int | float
    if operation == "sum":
        result = sum(numbers)
    elif operation == "product":
        result = 1
        for n in numbers:
            result *= n
    elif operation == "average":
        result = sum(numbers) / len(numbers)
    else:
        # This should never happen due to regex validation
        error_msg = f"Invalid operation: {operation}"
        logger.error(f"Task {self.request.id} failed: {error_msg}")
        raise ValueError(error_msg)

    logger.info(
        f"Task {self.request.id} completed: {operation}={result} ({len(numbers)} numbers)"
    )

    return {"operation": operation, "result": result, "count": len(numbers)}
