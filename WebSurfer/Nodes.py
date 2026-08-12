from State import WebState ,PageState
from utils import get_page_details
from ChatModel import OpenVINOChatModel
from utils import get_locators ,get_k_relevant_elements,resolve_locator_by_vote, click_and_check_mutation
from prompts import get_action_prompts ,get_mutation_prompt ,get_page_purpose_prompt ,get_task_completion_prompt
from collections import defaultdict
from langchain_core.messages import ToolMessage
from io import BytesIO
from PIL import Image
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from mytool import get_tools,get_screenshot,scroll_mouse
import asyncio
import copy
import json
import uuid
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()
import os
api_key = os.environ["groq_api_key"]
llmqwen=ChatGroq(model="qwen/qwen3.6-27b",api_key=api_key)
llmqwenstruc=llmqwen.with_structured_output(method='json_mode')

llmllama=ChatGroq(model="llama-3.1-8b-instant",api_key=api_key)
llmllamastruct=llmllama.with_structured_output(method='json_mode')

llmopenai=ChatGroq(model="openai/gpt-oss-120b",api_key=api_key)
llmstruct=llmopenai.with_structured_output(method='json_mode')

async def Page_details(state:WebState):
    print(f" total pages in pagedata : {len(state['pageData'])}")
    pageData=state['pageData'][-1]
    url=pageData['url']
    title=pageData['title']
    mutated=pageData.get('isMutated',False)
    page=pageData.get("page",None)
    if not mutated:
        # fresh load — this IS "initialize a new page"
        if not page:
            await page.goto(url)
        elements = await get_page_details(page)
        top_k_elem = get_k_relevant_elements(
                state["task"],
                elements,
                state["embedder"],
                5,
            )
        #print("top k elements : ",top_k_elem)
        previous_page_tasks = []

        for pg in state.get("pageData", []):
            pt = pg.get("pageTask")

            if not pt:
                continue

            if hasattr(pt, "content"):
                pt = pt.content
                previous_page_tasks.append(str(pt))
            elif isinstance(pt,str):
                previous_page_tasks.append(str(pt))

        previous_tasks_text = " , ".join(previous_page_tasks)

        prp = get_page_purpose_prompt(
            state["task"],
            url,title,top_k_elem,previous_tasks_text
        )
        # print('get purpose print ',prp)
        # task_for_this_page=await state['llm'].ainvoke([HumanMessage(content=prp)])
        task_for_this_page=await llmllamastruct.ainvoke(prp)
        print(task_for_this_page)
        pageData['pageTask']=task_for_this_page["pageTask"]
        pageData['elements']=elements
        return {}

    elements=await get_page_details(page)
    pageData['elements']=elements

    print("after mutation on page details")
    return {}

import json

from io import BytesIO
from PIL import Image
from langchain_core.messages import HumanMessage, ToolMessage ,SystemMessage





async def get_actions(state: WebState):
    pageData=state['pageData'][-1]
    elem = pageData["elements"]
    original_task=state['task']
    task=pageData['pageTask']
    page=pageData['page']
    pageActions=pageData.get('actions',[])
    pageCompletedActions=pageData.get('completed_actions',[])
    pageIncompletedActions=pageData.get('incompleted_actions',[])
    
    mutation = ""
    mutated = pageData.get("isMutated", False)
    top_k_elem = get_k_relevant_elements(
        original_task+" " +task,
        elem,
        state["embedder"],
        5,
    )


    if mutated:
        print("get action after mutation ...")
        mutation = get_mutation_prompt(
            original_task+" " +task,
            pageIncompletedActions,
            pageCompletedActions,
            pageActions,
            top_k_elem,
        )

    else:
        print('get action normal ')

    # Copy the list so state is not modified accidentally.
    local_messages = list()
    page = pageData["page"]
    screenshot_calls_used = 0
    max_screenshot_calls = 2
    scroll_state = await page.evaluate("""
        () => ({
            scrollY: window.scrollY,
            viewportHeight: window.innerHeight,
            documentHeight: document.documentElement.scrollHeight
        })
        """)
    
    while True:
        
        prp=get_action_prompts(
                    original_task=original_task,
                    task=task,
                    url=page.url,
                    title=await page.title(),
                    elements=top_k_elem,
                    mutation_prompt=mutation,
                    scroll_y=scroll_state["scrollY"],
                    viewport_height=scroll_state["viewportHeight"],
                    document_height=scroll_state["documentHeight"],
                )
        if mutated:
            local_messages.append(mutation)
        #print('current non mutated prompt : ',prp)

        call_msg = [
                HumanMessage(content=prp),
                *local_messages,
            ]
        print('total messages inside llm : ',len(call_msg))
        # response = await llm_with_tools.ainvoke(
        #     call_msg
        # )
        response=await llmstruct.ainvoke(call_msg)
        actions=response.get("actions",[])
        tool_calls=response.get("tool_calls",[])
        print("current_response:", response)

        native_tool_calls = tool_calls
        if native_tool_calls:
            tool_calls = native_tool_calls
            native_call = True
            
        else:
            pageData['actions']=actions #response.actions if response.actions else []
            return {}

        # Your prompt should request only one observation at a time.
        tool_call = tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})
        tool_call_id = tool_call.get("id",str(uuid.uuid4()))

        if tool_name == "get_screenshot":
            if screenshot_calls_used >= max_screenshot_calls:
                message = (
                    "Screenshot limit reached. Decide using the available "
                    "page elements and previous observations."
                )

                local_messages.append(
                        HumanMessage(content=observation_content)
                    )

                continue

            print("Taking screenshot...")

            img_bytes = await page.screenshot(type="png")
            image = Image.open(BytesIO(img_bytes))
            image.thumbnail((720, 720), Image.Resampling.LANCZOS)
            
            encoded_image = image
            screenshot_calls_used += 1

            observation_content = [
                        {
                            "type": "text",
                            "text": """
                    A screenshot of the current browser viewport is attached.

                    Inspect it together with CURRENT AVAILABLE ELEMENTS and decide the next
                    action required to progress the user's task.

                    Rules:
                    1. Do not request get_screenshot again for this unchanged URL and viewport.
                    2. The screenshot provides visual context but does not create DOM indices.
                    3. Every type, click, or get_text action must use an index appearing
                    literally in CURRENT AVAILABLE ELEMENTS.
                    4. If the required indexed element is available, return the next action.
                    5. If relevant content is outside the viewport, request scroll_mouse.
                    6. If the screenshot shows the required element but CURRENT AVAILABLE
                    ELEMENTS omits it, return a blocked response. Never invent an index.
                    7. Return only valid JSON containing exactly one of:
                    actions, tool_calls, or blocked.

                    Inspect the attached screenshot and make the next decision.
                    """.strip(),
                        },
                        {
                            "type": "image",
                            "image": encoded_image,
                            # "mime_type": "image/png",
                        },
                    ]

            # if native_call:
            #     local_messages.extend([
            #         response,
            #         ToolMessage(
            #             content=observation_content,
            #             name=tool_name,
            #             tool_call_id=tool_call_id,
            #         ),
            #     ])
            # else:
            #     # The model returned JSON text, not an actual AIMessage tool call.
            #     local_messages.extend([
            #         response,
            #         HumanMessage(content=observation_content),
            #     ])
            local_messages=[HumanMessage(content=observation_content)]

        elif tool_name == "scroll_mouse":
            pixels = int(tool_args["pixels"])

            await page.mouse.wheel(0, pixels)

            # Re-read actual position instead of assuming exact wheel movement.
            scroll_state = await page.evaluate("""
                () => ({
                    scrollY: window.scrollY,
                    viewportHeight: window.innerHeight,
                    documentHeight: document.documentElement.scrollHeight
                })
            """)

            # DOM/view changed, so old screenshot is stale.
            local_messages = [
                HumanMessage(
                    content=f"Page scrolled by {pixels}px. Re-evaluate the current viewport."
                )
            ]

            # Ideally refresh elements after scroll too.
            elem = await get_page_details(page)

            top_k_elem = get_k_relevant_elements(
                original_task + " " + task,
                elem,
                state["embedder"],
                5,
            )

            pageData["elements"] = elem

        else:
            raise ValueError(
                f"Unknown observation tool: {tool_name}"
            )
            # # Important: parse the DOM again after scrolling.
            # elem = await get_page_elements(page)

            # top_k_elem = get_k_relevant_elements(
            #     state["task"],
            #     elem,
            #     state["embedder"],
            #     10,
            # )

            # prp = get_action_prompts(
            #     state["task"],
            #     page.url,
            #     await page.title(),
            #     top_k_elem,
            #     mutation,
            # )
        return {}

from langgraph.types import Send
from langgraph.graph import StateGraph, START, END

def action_router(state: WebState):
    pageData = state['pageData'][-1]
    comp, incomp = pageData.get("completed_actions", []), pageData.get("incompleted_actions", [])
    if comp and not incomp:
        return "IsTaskCompleted"
    if pageData.get('isMutated', False):
        return "get_page_details"
    return "IsTaskCompleted"

async def dispatch_actions(state: WebState):
    pageData=state['pageData'][-1]
    actions = pageData.get("actions", [])
    if not actions:return {}

    completed,uncompleted=[],[]
    page=pageData['page']
    elements=pageData['elements']
    new_pg=None
    mutated=False
    for i in range(len(actions)):
        await page.evaluate("""
                    () => {
                        window.__domChanged = false;
                        const observer = new MutationObserver(() => { window.__domChanged = true; });
                        observer.observe(document.body, { childList: true, subtree: true, attributes: true });
                        window.__domObserver = observer;
                    }
                """)
        data = await execute_single_action({"action": actions[i], 'page': page, 'elements': elements})
        print('data of payload ', data)

        try:
            await asyncio.sleep(5)
            await page.wait_for_function("window.__domChanged === true", timeout=10000)
            mutated=True
        except Exception:
            mutated = False

        if data['status'] == "completed":
            ans = {'action': actions[i], 'status': data['work']}
            pg = data.get("page", None)
            completed.append(ans)
            if pg:
                new_pg = pg
                title = await pg.title()
                break
        else:
            uncompleted.extend(actions[i:])
            break

        if mutated:
            print('mutate ho gya .................')
            uncompleted.extend(actions[i + 1:])   # whatever's left after this action is now unexecuted
            break
    
    pageData['incompleted_actions']=uncompleted
    pageData['completed_actions']=completed
    res=pageData.get('pageResult',[])
    pageData['pageResult']=res+completed
    pageData['isMutated']=mutated

    if new_pg:
        print(f'naya page aaya hai ........ {new_pg}')
        return {
            'pageResult':{pageData['url']:pageData['pageResult']},
            'pageData': [{'url': new_pg.url,'page':new_pg, 'title': title, 'elements': {}}],  # blank slate for the new page
        }

    # same page — only update the two action-tracking fields, leave everything else untouched
    return {
        'pageResult':{pageData['url']:pageData['pageResult']},
    }
    

async def execute_single_action(payload):
    action = payload["action"]
    page = payload["page"]
    elements = payload["elements"]

    if action['action'] == "press_key":
        old_url = page.url
        try:
            print(f'pressing key {action["key"]}')

            popup_task = asyncio.create_task(page.context.wait_for_event("page", timeout=5000))
            nav_task = asyncio.create_task(page.wait_for_url(lambda url: url != old_url, timeout=5000))

            await page.keyboard.press(action['key'])

            done, pending = await asyncio.wait(
                [popup_task, nav_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            for t in pending:
                t.cancel()

            # did a new tab open?
            if popup_task in done and not popup_task.exception():
                new_page = popup_task.result()
                await new_page.wait_for_load_state("networkidle")
                title = await new_page.title()
                return {
                    'page': new_page,
                    'work': f'pressed {action["key"]}, opened new tab {new_page.url}',
                    'status': 'completed'
                    
                }

            # did the same tab navigate?
            if nav_task in done and not nav_task.exception():
                await page.wait_for_load_state("networkidle")
                return {'status': 'completed', 'work': f'pressed {action["key"]}, page navigated to {page.url}','page':page}

            # neither happened within timeout — key was pressed but caused no navigation (e.g. autocomplete dismiss)
            return {'status': 'completed', 'work': f'pressed {action["key"]}'}

        except Exception as e:
            print("press_key error:", e)
            return {'work': f'{e} error while pressing key', 'status': 'incomplete'}
    ids=action['index']
    data=await  get_locators(page,elements,ids)
    loca=await resolve_locator_by_vote(data)
    result={}
    try:
        if loca :
            locator=data[0]
            await asyncio.sleep(2)
            elem=""
            for k in elements.keys():
                if ids in elements[k].keys():
                    elem=elements[k][ids]
        
            if action['action']=="get_text":
                content=await locator.text_content()
                result['work']=f"extracted text {content[:400]} "
                result['status']='completed'
                return result
        
            elif action['action']=="type":
                text=action.get("text","")
                print(f'typing {text} ........................')
                await locator.fill(text)
                result['work']=f" typed {text} successfully." 
                result['status']='completed'
                return result
            
                
            elif action['action']=="click":
                if ids in elements['a'].keys() or ids in elements['button'].keys():
                    try:
                        print(f'pressing key {action["action"]}')
                    
                        popup_task = asyncio.create_task(page.context.wait_for_event("page", timeout=5000))
                        nav_task = asyncio.create_task(page.wait_for_url(lambda url: url != old_url, timeout=5000))
                    
                        await locator.click()
                    
                        done, pending = await asyncio.wait(
                            [popup_task, nav_task],
                            return_when=asyncio.FIRST_COMPLETED,
                        )
                        for t in pending:
                            t.cancel()
                    
                                # did a new tab open?
                        if popup_task in done and not popup_task.exception():
                            new_page = popup_task.result()
                            await new_page.wait_for_load_state("networkidle")
                            title = await new_page.title()
                            return {
                                'page': new_page,
                                'work': f'pressed {action["action"]}, opened new tab {new_page.url}',
                                'status': 'completed'
                                        
                            }
                    
                                # did the same tab navigate?
                        if nav_task in done and not nav_task.exception():
                            await page.wait_for_load_state("networkidle")
                            return {'status': 'completed', 'work': f'pressed {action["action"]}, page navigated to {page.url}','page':page}
                    
                                # neither happened within timeout — key was pressed but caused no navigation (e.g. autocomplete dismiss)
                        return {'status': 'completed', 'work': f'pressed {action["action"]}'}
                    
                    except Exception as e:
                        print("press_key error:", e)
                        return {'work': f'{e} error while clicking locator', 'status': 'incomplete'}
                        
                else:
                    await locator.click()
                    return {'work':f'clicked on {elem}','status':'completed'}
            else :
                return {'work':"no action because this action type does nor exist",'status':'incomplete'}
        else:
            return {'work':"element not found ",'status':'incomplete'}
    except Exception as e:
        return {'work':e,'status':'incomplete'}

async def isTaskCompleted(state: WebState):
    print("inside is task completed :::::")
    pageData = state['pageData']
    res = []
    for page in pageData:
        curr = ""
        for result in page.get('pageResult', []):
            curr += result['status']
        if curr:
            task_text = page['pageTask'].content if hasattr(page['pageTask'], 'content') else page['pageTask']
            curr = f" on this page {page['title']}, task of this page is {task_text} and we completed these tasks: " + curr
            res.append(curr)
    print("completed actions all over the state : ",res)
    prp = get_task_completion_prompt(state['task'], " ".join(res))
    # response = await state['llm'].ainvoke([HumanMessage(content=prp)])
    response=await llmstruct.ainvoke([HumanMessage(content=prp)])

    completed = False
    try:
        result = response
        completed = bool(result.get('completed', False))
        if completed:
            print(f'pageResult of state : {state["pageResult"]}')
    except Exception as e:
        print(f'got exception while loading json inside IsTaskCompleted node: {e}')

    return {"taskCompleted": completed}


def task_completion_router(state: WebState):
    if state.get("taskCompleted", False):
        return END
    return "get_page_details"