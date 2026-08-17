# from ChatModel import OpenVINOChatModel 
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
    url="https://www.google.com/about/careers/applications/"
    task='search software engineering job in banglore and get text of top 10 jobs . '
    
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
                'pageData':[{'url':url,'page':page,'title':await page.title(),"elements":{},'isMutated':False,'isCaptcha':False,"navigation_type":"never_navigated"}]
            }
        result=await graph.ainvoke(state)
        # print(result)
    await browser.close()
asyncio.run(main())
