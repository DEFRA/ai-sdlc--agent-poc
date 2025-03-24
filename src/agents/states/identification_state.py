"""State model for identification nodes."""

from typing import Optional

from pydantic import BaseModel


class IdentificationState(BaseModel):
    """State specific to identification factory nodes, containing only mutable fields."""

    data_model_files: Optional[list[str]] = None
    error: Optional[str] = None
