from Structure import PlanModel,SQLModel
from Prompts import SQLgen_prompt,build_sql_fix_prompt,not_feasible_prompt,get_output_prompt,feasibility_prompt,PlannerPrompt
from langgraph.types import Send
from langgraph.graph import END
from Models.llm import LLM
from Graph.SubGraphs.AnalystGraph.utils import get_schema, get_relevant_table
from DB.supabase import db
from AnalystGraphState import WorkerState,AnalystState,Feasible
import sqlglot
import time
import json
import os
from dotenv import load_dotenv

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
groq_api_key2 = os.getenv("GROQ_API_KEY2")

SQLGeneratorLLM=LLM(model_name="llama-3.3-70b-versatile",temperature=0.3,max_tokens=8000,api_key=groq_api_key2)
SQLCorrectorLLM=LLM(model_name="meta-llama/llama-4-scout-17b-16e-instruct",temperature=0.3,max_tokens=8000)
PlannerLLM=LLM(model_name="llama-3.3-70b-versatile",temperature=0.9,max_tokens=10000)
OutputLLM=LLM(model_name="openai/gpt-oss-120b",temperature=0.9,max_tokens=10000)
GeneralLLM=LLM(model_name="meta-llama/llama-4-scout-17b-16e-instruct",temperature=0.3,max_tokens=8000)
class SQLgenerator:
    def __init__(self,db=db):
        self.db = db
    def generate_sql(self,state:WorkerState):
        task = state.task
        a=time.time()
        for id, plan in task.items():
            prompt = SQLgen_prompt(state.user_query, plan, state.db_schema, state.dependencies)
            print(f' len of sql generator prompt {len(prompt)}')
            response = SQLGeneratorLLM.structured_invoke(prompt, SQLModel)
            print(f'time taken in generating sql for {id} is {time.time()-a} seconds')
            return {
                'sql_query': response.sql_query,
                'sql_query_description': response.description
            }
    
       
    def validate_sql(self,state:WorkerState):
        sql = state.sql_query
        try:
            sqlglot.parse_one(sql)
            return {
                'validation_status': True,
                'error_while_validation':""
            }
        except Exception as e:
            return {'validation_status': False, 'error_while_validation': str(e)}
        
    def Validation_Router(self,state:WorkerState):
        status = state.validation_status
        if status:
            return "SqlExecutor"
        return "SqlCorrector"
    

        
    def Execute_sql(self,state:WorkerState):
        sql=state.sql_query
        try:
            out=self.db.run(sql)
            print(f'Output type: {type(out)}')
            return {'output':out,'success':True,"error_while_execution":"",'execution_status':True}
        except Exception as e:
            return {
                'success':False,
                'error_while_execution':str(e),
                'execution_status':False
            }
    def Execution_Router(self,state:WorkerState):
        status = state.execution_status
        if status:
            return "To_parent"
        return "SqlCorrector"
    def Summarizer(self,state:WorkerState):
        output=state.output

        prompt=f"Summarize the following output in a concise manner:\n{output}"
        response=OutputLLM.invoke(prompt)
        return {'summary':response.content} 
    def Correct_sql(self,state:WorkerState):
        if state.MAX_RETRIES == 0:
            return {'success': False}
        plan, prev_sql = state.task, state.sql_query
        ids=state.ids
        error = ""
        if state.error_while_validation:
            error = state.error_while_validation
        else:
            error = state.error_while_execution
        prompt = build_sql_fix_prompt(plan[ids], error, prev_sql,state.db_schema)
        print(f' len of sql corrector prompt {len(prompt)}')
        try:
            response = SQLCorrectorLLM.structured_invoke(prompt, SQLModel)
        except Exception as e:
            response=SQLModel(**{'description':state.sql_query_description,"sql_query":state.sql_query})
            
        return {
            'sql_query': response.sql_query,
            'sql_query_description': response.description,
            'MAX_RETRIES': state.MAX_RETRIES - 1
        }
    def Retries_Check(self,state:WorkerState):
        status = state.success
        if status:
            return "SqlValidator"
        else:
            return END
    def to_parent(self,state:WorkerState):
        return {}
    
class Analyst:
        def __init__(self,db=db):
            self.db = db
        
        
        def feasibility(self,state=AnalystState):
            a=time.time()
            schema = json.dumps(get_schema()['connections'],indent=2)
            related_tables = get_relevant_table(state.query,db=self.db,top_k=10)
            print(type(schema))
            prompt=feasibility_prompt(state.query,schema,related_tables)
            print(f' len of feasibility prompt {len(prompt)}')
            response=GeneralLLM.structured_invoke(prompt,Feasible)    
            return {'feasiblity':response,'dbschema':schema,'related_tables':related_tables}
            
        def feasibility_router(self,state:AnalystState):
            if state.feasiblity.status=="POSSIBLE":
                return "PlanGenerator"
            else: return "Final"
        def generate_plan(self, state=AnalystState):  
            query=state.query
            prompt = PlannerPrompt(state.dbschema, state.related_tables, query)
            llm = PlannerLLM
            print(f' len of planner prompt {len(prompt)}')
            plan = llm.structured_invoke(prompt, PlanModel)
            print("plan generated>.......")
            dgraph={}
            for idx, subplan in plan.subPlans.items():
                if not subplan.depends_on:
                    dgraph[idx]=[]
                else:
                    dgraph[idx]=subplan.depends_on
            return {'plans': plan,'dependency_graph':dgraph}
       
        def prepare_ready_tasks(self,state:AnalystState):
            independent_subplans=list()
            for idx, subplan in state.plans.subPlans.items():
                if not subplan.depends_on and idx not in state.plan_result.keys() and idx not in state.succeed_plan and idx not in state.failed_plan:
                    independent_subplans.append(idx)
            if independent_subplans:
                return {"ready_tasks":independent_subplans}
            ready = []

            completed = set(state.plan_result.keys())
            for pid, subplan in state.plans.subPlans.items():
                print(f'checking plan id {pid} ........')
                if pid in completed:#here it can get stuck in loop if there is a plan which can not be completed.
                   
                    continue

                deps = set(subplan.depends_on)
                if deps.issubset(completed):
                    ready.append(pid)

            return {"ready_tasks": ready}
        def task_scheduler(self,state:AnalystState):
            
            completed = set(state.plan_result.keys())
            sends = []
            for pid ,sbplan in state.plans.subPlans.items():
                dependency_outputs={}
                if pid not in state.succeed_plan and pid not in state.failed_plan and pid not in state.plan_result:
                    
                    sbp=sbplan
                    if pid in completed:continue
                    deps=set(sbp.depends_on)
                    if deps.issubset(completed):
                        failed_deps=set(state.failed_plan)
                        for dep in deps:
                            if dep in failed_deps:
                                dependency_outputs = {
                                    dep: {"title":state.plans.subPlans[dep].title,"brief":state.plans.subPlans[dep].brief,"output": state.plan_result[dep],"error":state.plan_result[dep].get("error","Unknown error")}
                                    
                                } 
                            else:
                                dependency_outputs = {
                                    dep: {"title":state.plans.subPlans[dep].title,"brief":state.plans.subPlans[dep].brief,"output": state.plan_result[dep]}
                                    
                                }                        
                    sends.append(
                            Send(
                                "WorkerSubgraph",
                                {
                                    "ids": pid,
                                    "task": {pid: sbp},
                                    "dependencies": dependency_outputs,
                                    "user_query": state.query,
                                    "db_schema": state.dbschema,
                                }
                            )
                        )
                
            # Return a Command to schedule sends; langgraph expects a dict/Command, not raw Send list
            if  sends:
                print('scheduling tasks')
                return sends
            
            return "Final"
            
        def scheduler_router(self,state:AnalystState):
            sends=self.task_scheduler(state)
            if sends:return sends
            # No runnable tasks found. If there are unfinished tasks remaining,
            # we've hit a deadlock (no ready tasks); finalize to avoid infinite loop.
            return "Final"
                   
        def final(self,state:AnalystState):
            print('generating response ...')
            if state.feasiblity.status=="POSSIBLE":
                q={
                    "original_user_query":state.query,                    
                    }
                plans={}
                for idx,sbplan in state.plans.subPlans.items():
                    ttl=sbplan.title
                    brf=sbplan.brief
                    out="No output for this subplan may be some error"
                    if idx in state.plan_result.keys():
                        out=state.plan_result[idx]
                    plans[idx]={'title':ttl,"brief":brf,"output_of_subplan":out}
                error=[str(idx) for idx in state.failed_plan]
                data={"user query":q['original_user_query'],"sub Plans and thier details":plans,"error in subplan with their ids":error}

                prompt=get_output_prompt(data)
                print(f' len of output prompt {len(prompt)}')
                response=OutputLLM.invoke(prompt)
                print(response.content)
                return {'final_answer':response.content}
            f=state.feasiblity
            prompt=not_feasible_prompt(f.reason,f.possible_analysis,f.missing_requirements,f.alternative_queries)
            response=OutputLLM.invoke(prompt)
            print(response.content)
            return {'final_answer':response.content}
            
        