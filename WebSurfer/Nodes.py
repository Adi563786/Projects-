from State import WebState ,PageState
from utils import get_page_details
from ChatModel import OpenVINOChatModel
from utils import get_locators ,get_k_relevant_elements,resolve_locator_by_vote, click_and_check_mutation
from prompts import get_action_prompts ,get_mutation_prompt
from collections import defaultdict
from langchain_core.messages import ToolMessage
from io import BytesIO
from PIL import Image
import copy
from mytool import get_tools,get_screenshot,scroll_mouse
import asyncio
import copy
import json
import uuid
async def Page_details(state):
    page = state["page"]
    mutated = state.get("mutated", False)
    current = state.get("current_page", {}) or {}

    if not mutated:
        # fresh load — this IS "initialize a new page"
        await page.goto(state["url"])
        elements = await get_page_details(page)
        title = await page.title()
        return {
            "current_page": {"url": page.url, "title": title, "elements": elements},
            "mutated": False,
        }

    # mutated == True: do NOT navigate — use the page object as-is
    elements = await get_page_details(page)

    title = await page.title()
    new_current = {"url": page.url, "title": title, "elements": elements}

    same_page_mutation = "completed_actions" in current

    if same_page_mutation:
        # carry the action bookkeeping forward so get_actions can build the mutation prompt
        new_current["actions"] = current.get("actions", [])
        new_current["completed_actions"] = current.get("completed_actions", [])
        new_current["incompleted_actions"] = current.get("incompleted_actions", [])
        return {
            "current_page": new_current,
            "previous_page": copy.deepcopy(current),
            "mutated": True,
        }

    # navigation case — previous_page was already correctly set by dispatch_actions; leave it alone
    return {
        "current_page": new_current,
        "mutated": True,
    }

# async def page_validator_url_title(state:WebState):
    
#     url,title,task=state['url'],state['current_page']['title'],state['task']
#     prompt=f"""you are a page validator , your task is to determine whether page is valid for the given task is or not . Task is : {task} , current page url : {url} and title of the page is : {title} . return only valid json no explaination . For example  if page is valid {{"IsValid":True}}"""
#     response=await state['llm'].ainvoke(state['messages'],prompt)
#     return {
#         'messages':[response]
#     }

import base64
import json

from io import BytesIO
from PIL import Image
from langchain_core.messages import HumanMessage, ToolMessage ,SystemMessage





async def get_actions(state: WebState):
    elem = state["current_page"]["elements"]

    top_k_elem = get_k_relevant_elements(
        state["task"],
        elem,
        state["embedder"],
        10,
    )

    mutation = ""
    mutated = state.get("mutated", False)

    if mutated:
        mutation = get_mutation_prompt(
            state["task"],
            state["current_page"]["incompleted_actions"],
            state["current_page"]["completed_actions"],
            state["current_page"]["actions"],
            top_k_elem,
        )
        # print('mutation prompt aa gya ::: ',mutation)

    

    llm_with_tools = state["llm"].bind_tools(get_tools)

    # Copy the list so state is not modified accidentally.
    local_messages = list(state["messages"])
    # sys_msg=SystemMessage(
    #     content=prp if prp else mutation
    # )
    page = state["page"]
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
                    task=state["task"],
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
        # print("local -messages :",local_messages)
        # print("prp length:", len(prp))
        # print('current prp: ',prp)

        call_msg=[SystemMessage(content=prp),*local_messages]
        print("previous message:",call_msg[-1])
        # for index, message in enumerate(call_msg):
        #     print(
        #         index,
        #         type(message).__name__,
        #         "content_length=",
        #         len(str(message.content)),
        #         repr(str(message.content)[:300]),
        #     )
        response = await llm_with_tools.ainvoke(
            call_msg
        )

        print("current_response:", response)

        native_tool_calls = response.tool_calls
        # native_action_calls=response.get("actions",[])
        if native_tool_calls:
            tool_calls = native_tool_calls
            native_call = True
        # elif native_action_calls:

        #     # native_call = False

        #     # try:
        #     #     parsed_content = json.loads(response.actions)
        #     # except (json.JSONDecodeError, TypeError) as exc:
        #     #     print("Could not parse response for actions :", exc)
        #     #     return {"messages": [response]}

        #     # action_calls = parsed_content.get("actions", [])

        #     # This is probably an {"actions": [...]} response.
        #     # if not action_calls:
        #     print('generated actions now going for dispatch actions')
        #     return {"messages": [response]}
            
        else:
            return {"messages":[response]}

        # Your prompt should request only one observation at a time.
        tool_call = tool_calls[0]
        # print(tool_call)
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

            if native_call:
                local_messages.extend([
                    response,
                    ToolMessage(
                        content=observation_content,
                        name=tool_name,
                        tool_call_id=tool_call_id,
                    ),
                ])
            else:
                # The model returned JSON text, not an actual AIMessage tool call.
                local_messages.extend([
                    response,
                    HumanMessage(content=observation_content),
                ])

        elif tool_name == "scroll_mouse":
            pixels = int(tool_args["pixels"])

            print(f"Scrolling by {pixels} pixels...")
            await page.mouse.wheel(0, pixels)

            direction = "down" if pixels > 0 else "up"
            observation = (
                f"The page was scrolled {direction} by {abs(pixels)} pixels. "
                "Re-evaluate the current page."
            )
            scroll_state['scrollY']+=pixels
            local_messages.append(
                HumanMessage(content=observation)
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
        
        else:
            raise ValueError(f"Unknown observation tool: {tool_name}")

from langgraph.types import Send
from langgraph.graph import StateGraph, START, END

def action_router(state:WebState):
    comp,incomp=state['current_page'].get("completed_actions",[]),state['current_page'].get("incompleted_actions",[])
    print("completed actions :",comp)
    print("incompleted actions :",incomp)
    if comp and not incomp:
        return END
    if state.get('mutated', False):
        return "get_page_details"
    return END

async def dispatch_actions(state: WebState):
    if hasattr(state['messages'][-1] ,'actions'):

        actions = state["messages"][-1].actions
        completed,uncompleted=[],[]
        page=state['page']
        elements=state['current_page']['elements']
        new_pg=None
        title=None
        await page.evaluate("""
                () => {
                    window.__domChanged = false;
                    const observer = new MutationObserver(() => { window.__domChanged = true; });
                    observer.observe(document.body, { childList: true, subtree: true, attributes: true });
                    window.__domObserver = observer;
                }
            """)
        mutated=False
        for i in range(len(actions)):
            data = await execute_single_action({"action": actions[i], 'page': page, 'elements': elements})
            print('data of payload ', data)

            try:
                ele=await get_page_details(page)
                # for k, v in ele.items():
                #     if k=='input':print("element befor mutation  of inputs :",v)
                #     if k=="button":print("element before mutation  of button :",v)
                await asyncio.sleep(5)
                await page.wait_for_function("window.__domChanged === true", timeout=10000)
                mutated = True
                # ele=await get_page_details(page)
                # for k, v in ele.items():
                #     if k=='input':print("element after mutation of inputs :",v)
                #     if k=="button":print("element after mutation  of button :",v)
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
        
        if new_pg:
            old_page_state = {
                **state["current_page"],
                "actions": actions,
                "completed_actions": completed,
                "incompleted_actions": uncompleted,
            }
            return {
                'visited': [page.url],
                'url': new_pg.url,
                'page': new_pg,  
                'result': [{page.url: completed}],
                'previous_page': old_page_state,          # old page's full data, snapshotted here
                'current_page': {'url': new_pg.url, 'title': title, 'elements': {}},  # blank slate for the new page
            }

        # same page — only update the two action-tracking fields, leave everything else untouched
        page_state = {
            **state["current_page"],
            "actions": actions,
            "completed_actions": completed,
            "incompleted_actions": uncompleted,
        }
        return {
            "mutated": mutated,
            "current_page": page_state,
        }
    return "end"
async def execute_single_action(payload):
    #print("executing : ",payload)
    action = payload["action"]
    page = payload["page"]
    elements = payload["elements"]
    # print(elements)
    if action['action']=="press_key":
        old_url=page.url
        try:
            print(f'pressing keys  {action["key"]}')
            async with page.context.expect_page(timeout=10000) as new_page_info:
                await page.keyboard.press(action['key'])
            new_page=await new_page_info.value
            await new_page.wait_for_load_state('networkidle')
            result['work']=f' press key {action["key"]} and went to the {new_page.url}'
            result['status']='completed'
            title=await new_page.title()
            return {'page':new_page,'work':result["work"],'status':result['status'],'current_page':{"url":new_page.url,"title":title,'elements':{}}}
        except TimeoutError:    
            print("keys presssed but not page changed .......")                                
            try:
                await page.wait_for_url(
                    lambda url: url != old_url,
                    timeout=3000
                )
            except TimeoutError:
                pass
    
            await page.wait_for_load_state("networkidle")
            return {'status':"completed",'work':"it wasn't the press key to change page "}
        except Exception as e:
            print("keys presssed but errror aa gya ")
            return {'work':f'{e} error while visiting to next page','status':'incomplete'}
    ids=action['index']
    data=await  get_locators(page,elements,ids)
    # print(data)
    loca=await resolve_locator_by_vote(data)
    # print("locator by wote : ",loca)
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
                result['work']=f"extracted text {content[:30]} from {elem}"
                result['status']='completed'
                return result
        
            elif action['action']=="type":
                text=action.get("text","")
                print(f'typing {text} ........................')
                await locator.fill(text)
                result['work']=f" typed {text[:20]} inside {elem}" 
                result['status']='completed'
                return result
            
                
            elif action['action']=="click":
                if ids in elements['a'].keys():
                    try:
                        async with page.context.expect_page(timeout=10000) as new_page_info:
                            await locator.click()
                        new_page=await new_page_info.value
                        await new_page.wait_for_load_state("networkidle")
                        result['work']=f'clicked on {elem} and went to the {new_page.url}'
                        result['status']='completed'
                        title=await new_page.title()
                        return {'page':new_page,'work':result['work'],'status':result['status'],'current_page':{"url":new_page.url,"title":title,'elements':{}}}
                    except TimeoutError:
                        print(f'timeout error while visiting {elem} page')
                        return {'work':f'timeout error while visiting {elem} page','status':'incomplete'}
                    except Exception as e:
                        return {'work':f'{e} error while visiting {elem} page','status':'incomplete'}
                        
                else:
                    await locator.click()
                    return {'work':f'clicked on {elem}','status':'completed'}
            else :
                return {'work':"no action because this action type does nor exist",'status':'incomplete'}
        else:
            return {'work':"element not found ",'status':'incomplete'}
    except Exception as e:
        return {'work':e,'status':'incomplete'}
                
# async def tool_router(state:WebState):
#     last_message=state['messages'][-1]
#     if  last_message.tool_calls:
#         return 'tool_call'
#     elif last_message.actions:
#         return    "Dispatch_actions"
#     else:
#         return END