from typing import TypedDict , List ,Set ,Sequence , Annotated ,Dict,Any
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage
from ChatModel import OpenVINOChatModel

class PageState(TypedDict):
    url:str
    title:str
    elements: Dict[str, Dict[str, str]] # {"a":{"index_number":{"role":"a","name":meow}}}
    actions:List[Dict[str,str]]
    completed_actions=Annotated[List[Dict[str,str]],add_messages]
    incompleted_actions=Annotated[List[Dict[str,str]],add_messages]



class WebState(TypedDict):
    mutated:bool=False
    url:str
    task:str
    messages:Annotated[List[BaseMessage],add_messages]
    llm:Any
    browser_context:Any
    page:Any
    visited:Annotated[List[str],add_messages]
    valid_page:bool=False
    result:Annotated[List[Dict[str,List[str]]],add_messages]
    current_page:PageState
    previous_page:PageState
    embedder:Any

    