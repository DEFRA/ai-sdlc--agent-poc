"""State model for analysis nodes."""

from typing import Optional

from pydantic import BaseModel


class AnalysisState(BaseModel):
    """State specific to analysis factory nodes, containing only mutable fields."""

    data_model_files: list[str]
    data_model_analysis: Optional[str] = None
    error: Optional[str] = None
