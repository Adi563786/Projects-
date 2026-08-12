from typing import TypedDict , List ,Set ,Sequence , Annotated ,Dict,Any
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage
from ChatModel import OpenVINOChatModel

def append_or_replace_last(existing: list, new) -> list:
    """Append a new PageState, or if new is a partial update dict, merge it into the last entry."""
    if not existing:
        return [new] if not isinstance(new, list) else new
    if isinstance(new, list):
        return existing + new
    # merge partial update into the last PageState instead of appending a duplicate
    merged_last = {**existing[-1], **new}
    return existing[:-1] + [merged_last]


class PageState(TypedDict):
    pageTask:str
    url:str
    title:str
    page:Any
    elements: Dict[str, Dict[str, str]] # {"a":{"index_number":{"role":"a","name":meow}}}
    actions:List[Dict[str,str]]
    completed_actions=List[Dict[str,str]]
    incompleted_actions=List[Dict[str,str]]
    isMutated:bool=False
    isCaptcha:bool=False
    pageResult:List[Dict[str,str]]
    top_k_elements:Dict[str,Dict[str,Dict[str,str]]]


class WebState(TypedDict):
    url:str
    task:str
    messages:Annotated[List[BaseMessage],add_messages]
    llm:Any
    browser_context:Any
    pageResult:Dict[str,Dict[str,List[Dict[str,str]]]]
    pageData:Annotated[List[PageState],append_or_replace_last]
    embedder:Any
    taskCompleted:bool=False

    