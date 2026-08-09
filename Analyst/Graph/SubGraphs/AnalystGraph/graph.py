import time 
strt=time.time()
print('starteddd...............')
import sys
from pathlib import Path

# Ensure project root is on sys.path so package imports work when running as a script
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from langgraph.graph import StateGraph, START, END
from AnalystGraphState import AnalystState, WorkerState
from Nodes import Analyst, SQLgenerator
print("all libs and modules are loaded .........")
analyst=Analyst()
sql_handler=SQLgenerator()
graph=StateGraph(AnalystState)
worker=StateGraph(WorkerState)

def run_worker_subgraph(worker_input):
            result=WorkerSubgraph.invoke({
                'ids':worker_input['ids'],
                'task':worker_input['task'],
                'dependencies':worker_input['dependencies'],
                'user_query':worker_input['user_query'],
                'db_schema':worker_input['db_schema']
            })
            pid=result['ids']
            if result.get("success") is True and result.get("execution_status") is True:
                return {
                    "plan_result": {
                        pid: result.get("output")
                    },
                    "succeed_plan": [pid],
                    
                }

            return {
                "plan_result": {
                        pid: {
                            "error": (
                                result.get("error_while_execution")
                                or result.get("error_while_validation")
                                or "Unknown worker error"
                            )
                        }
                    },
                    "failed_plan": [pid]
                } 

# worker nodes
worker.add_node("SqlGenerator",sql_handler.generate_sql)
worker.add_node("SqlValidator",sql_handler.validate_sql)
worker.add_node("SqlCorrector",sql_handler.Correct_sql)
worker.add_node("SqlExecutor",sql_handler.Execute_sql)
worker.add_node("To_parent",sql_handler.to_parent)
#worker graph edges
worker.add_edge(START,"SqlGenerator")
worker.add_edge("SqlGenerator",'SqlValidator')
worker.add_conditional_edges("SqlValidator",sql_handler.Validation_Router)
worker.add_conditional_edges("SqlExecutor",sql_handler.Execution_Router)
worker.add_edge("SqlCorrector","SqlValidator")
worker.add_edge("To_parent",END)

WorkerSubgraph=worker.compile()




#analyst nodes
graph.add_node("Feasibility",analyst.feasibility)
graph.add_node("PlanGenerator", analyst.generate_plan)
graph.add_node("GetReadyTask", analyst.prepare_ready_tasks)
graph.add_node("Final",analyst.final)
graph.add_node("WorkerSubgraph", run_worker_subgraph)


graph.add_edge(START, "Feasibility")
graph.add_conditional_edges("Feasibility",analyst.feasibility_router)
graph.add_edge("PlanGenerator","GetReadyTask")
graph.add_conditional_edges("GetReadyTask",analyst.scheduler_router)
graph.add_edge("WorkerSubgraph","GetReadyTask")
graph.add_edge("Final",END)

analyst_graph=graph.compile()
initial_state = {
	"query": "What products and product categories are most popular in each city and country,",
	"plans": None,
	"schema": "",
	"related_tables": [],
	"plan_result": {},
	"succeed_plan": [],
	"failed_plan": [],
	"feasiblity": None,
}

print("graph started ")
resp = analyst_graph.invoke(initial_state)

print(f'completion time {time.time()-strt}')