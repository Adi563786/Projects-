import operator

from pydantic import BaseModel,Field
from typing import Dict, List, Any, Optional, Annotated, TypedDict,Set,Literal

from Structure import PlanModel, SubPlan

class Feasible(BaseModel):
    status:Literal['POSSIBLE',"NOT_POSSIBLE"]
    reason:str
    possible_analysis:List[str]
    missing_requirements:List[str]
    alternative_queries:List[str]

class WorkerState(BaseModel):
    MAX_RETRIES: int = 3
    user_query: str
    db_schema: Optional[str] = None
    relevant_table: Optional[List[str]] = None
    task: Optional[Dict[str, SubPlan]] = None
    ids: Optional[str] = None
    dependencies:Optional[Dict[str,Any]]=None
    sql_query: Optional[str] = None
    sql_query_description: Optional[str] = None
    output: Optional[Any] = None
    success: bool = Field(default=True)
    validation_status: bool = Field(default=False)
    execution_status:bool=Field(default=False)
    error_while_validation: Optional[str] = None
    error_while_execution: Optional[str] = None
    
class AnalystState(BaseModel):
    query: str
    plans: Optional[PlanModel]
    dbschema:Optional[str]=""
    ready_tasks:Optional[List[str]]=[]
    dispatched_task:List[str]=[]
    related_tables:Optional[List[str]]
    dependency_graph:Optional[Dict[str,List[Any]]]=None
    plan_result: Annotated[Dict[str, Any], operator.or_]
    succeed_plan: Annotated[List[str], operator.add] = []
    failed_plan: Annotated[List[str], operator.add] = []
    final_answer:Optional[str]=""
    feasiblity:Optional[Feasible]

