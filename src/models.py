from pydantic import BaseModel, Field

from typing import Optional, List


class MetricInput(BaseModel):
    hours: Optional[float] = None
    technical_complexity: Optional[int] = Field(None, ge=1, le=10)
    manual_effort: Optional[int] = Field(None, ge=1, le=10)
    uncertainty_level: Optional[int] = Field(None, ge=1, le=10)
    