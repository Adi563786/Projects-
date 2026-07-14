from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

class SQLModel(BaseModel):  

    description: str

    sql_query: Optional[str] = Field(
        default=None,
        description="Full executable PostgreSQL query, including WITH clauses if needed, ending with semicolon."
    )
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict

class OutputControl(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_rows: int = Field(default=100, ge=0, le=100)
    allow_raw_rows: bool = False
    @field_validator("max_rows", mode="before")
    @classmethod
    def clamp_max_rows(cls, v):
        if v is None:
            return 100
        return min(max(int(v), 0), 100)
class SubPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    brief: str
   
    related_table: List[str] = Field(
        ...,
        description="Only tables required for this analytical task."
    )

    required_columns: List[str] = Field(
        ...,
        description="All schema columns required: metrics, dimensions, date columns, filters, and join keys."
    )

    metrics: List[str] = Field(
        default_factory=list,
        description="Business metrics needed for this task. Use real schema columns or derived metric names only when derivable."
    )

    dimensions: List[str] = Field(
        default_factory=list,
        description="Grouping or comparison columns such as quarter, category, product, region."
    )

    filters: List[str] = Field(
        default_factory=list,
        description="Business filters required for this task."
    )

    grain: str = Field(
        default="",
        description="The aggregation level, for example quarter, category-quarter, product-quarter."
    )
    ranking: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Ranking details if this task requires ranking. Should include entity, metric, and top_n."
    )
    depends_on: Optional[List[int]] = []

    output: Dict[str, Any] = Field(
        ...,
        description="Expected output columns with data types."
    )

    assumptions: List[str] = Field(
        default_factory=list,
        description="Any assumptions or data gaps."
    )

    output_control: Optional[OutputControl] = None


    
class PlanModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goal: str
    subPlans: Optional[Dict[str,SubPlan]]
    def find_plan_by_ids(self,ids):
        return self.subPlans.get(ids)
