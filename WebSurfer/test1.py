from ChatModel import OpenVINOChatModel 
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage,BaseMessage,AIMessage ,SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState , add_messages
from langgraph.prebuilt import ToolNode
from typing import TypedDict ,Annotated,Sequence
from playwright.async_api import async_playwright
from State import WebState ,PageState
import asyncio

from sentence_transformers import SentenceTransformer


from Nodes import Page_details, get_actions, action_router, dispatch_actions, isTaskCompleted, task_completion_router

builder = StateGraph(WebState)
builder.add_node("get_page_details", Page_details)
builder.add_node("Dispatch_actions", dispatch_actions)
builder.add_node("get_actions", get_actions)
builder.add_node("IsTaskCompleted", isTaskCompleted)

builder.add_edge(START, 'get_page_details')
builder.add_edge("get_page_details", "get_actions")
builder.add_edge("get_actions", "Dispatch_actions")

builder.add_conditional_edges(
    "Dispatch_actions",
    action_router,
    {
        "get_page_details": "get_page_details",
        "IsTaskCompleted": "IsTaskCompleted",
    },
)

builder.add_conditional_edges(
    "IsTaskCompleted",
    task_completion_router,
    {
        "get_page_details": "get_page_details",
        END: END,
    },
)

graph = builder.compile()
# builder.add_edge("Dispatch_actions",END)
# builder.add_edge("action_router","action_router")
# builder.add_edge("execute_actions",END)
graph=builder.compile()

async def main():
    embedder = SentenceTransformer("all-MiniLM-L6-v2")  # small, fast, local
    url="https://www.credentinfotech.com/"
    task='contact them and send some message with random data do not hit submit'
    
    # llm=OpenVINOChatModel(r"C:\Users\aditya maurya\Desktop\prj\qwen2.5_vl_7B_int4")
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=False)
        context=await browser.new_context()
        page=await context.new_page()
        await page.goto(url)
        state = {
                "task": task,
                "messages":[],
                "url": url,
                # "llm": llm,
                'embedder':embedder,
                'pageData':[{'url':url,'page':page,'title':await page.title(),"elements":{},'isMutated':False,'isCaptcha':False}]
            }
        result=await graph.ainvoke(state)
        # print(result)
    await browser.close()
asyncio.run(main())


# @tool
# def get_weather(city:str):
#     """Returns weather of a city """
#     return f'its raining in {city}'
# @tool
# def get_stock_price(stock:str):
#     """returns stock price of the stock"""
#     return "220 dollars"

# # tools=ToolNode([get_weather,get_stock_price])
# # llm=llm.bind_tools([get_weather,get_stock_price])

# class AgentState(TypedDict):
#     messages:Annotated[Sequence[BaseMessage],add_messages]

# message = [HumanMessage(
    
    
# )]


# def call_llm(state:AgentState):
#     response=llm.invoke(state["messages"])
#     return {'messages':[response]}


# def route_to_tools(state:AgentState):
#     last_message = state["messages"][-1]
#     if not last_message.tool_calls:
#         return 'end'
#     else:return "tool_call"

# builder=StateGraph(AgentState)
# builder.add_node('assistant',call_llm)
# builder.add_node(
#     "tools",
#     tools
# )

# builder.add_edge(START,'assistant')
# builder.add_conditional_edges(
#     "assistant",
#     route_to_tools,
#     {
#         "tool_call": "tools",
#         'end': END,
#     },
# )
# builder.add_edge(START,'assistant')
# builder.add_edge("tools",'assistant')
# graph=builder.compile()
# result=graph.invoke({"messages":message})