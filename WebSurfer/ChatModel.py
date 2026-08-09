from langchain_core.language_models.chat_models import BaseChatModel
# import openvino_genai as ov_genai
from transformers import AutoProcessor ,TextStreamer
from optimum.intel.openvino import OVModelForVisualCausalLM ,OVModelForCausalLM
from langchain_core.messages import (AIMessage,HumanMessage,SystemMessage,BaseMessage,ToolMessage)
from langchain_core.outputs import ChatGeneration, ChatResult
import json 
import re
import asyncio
import uuid
from typing import Sequence , Any
# from utils import execute_action

class OpenVINOChatModel(BaseChatModel):
    def __init__(self, model_path,max_length=2048,device="GPU"):
        super().__init__()
        self._processor = AutoProcessor.from_pretrained(model_path)
        self._model = OVModelForVisualCausalLM.from_pretrained(model_path, device=device)        
        self._tools=[]
        self._max_len=max_length
        

    @property
    def _llm_type(self):
        return "openvino"
    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        import copy
        new_model = copy.copy(self)
        new_model._tools = tools
        return new_model
    def extract_content(self, content):
        texts = []
        images = []
        if isinstance(content, str):
            texts.append(content)

        elif isinstance(content, list):
            for item in content:
                if item["type"] == "text":
                    texts.append(item["text"])

                elif item["type"] == "image":
                    images.append(item["image"])

        return "\n".join(texts), images
    def to_text(self,content):
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        parts.append(item["text"])
                else:
                    parts.append(str(item))
            return "\n".join(parts)

        return str(content)
    def _generate_sync(self,inputs):
        streamer=TextStreamer(
            self._processor.tokenizer,skip_prompt=True,skip_special_tokens=True,
        )
        return self._model.generate(
            **inputs,streamer=streamer,max_new_tokens=self._max_len,do_sample=False
        )
    
    def _build_prompt(self,messages,prompt):
        
        # if self._tools:
        #     prompt+="\n Available tools \n"
        #     for tool in self._tools:
        #         prompt+=f"""
        #                 Tool:
        #                 Name: {tool.name}
        #                 Description:{tool.description}
        #                 Arguments:{tool.args}\n
        #                 """
        #     prompt+="""If a tool is required output ONLY JSON .
                
        #         Example:
        #         {"actions"=[
        #             {
        #                 "action":"click",
        #                 "index":25
        #             }
        #         ]}
        #         otherwise answer normally.
        #         """
        conversation = []
        if isinstance(self._model,OVModelForCausalLM):
            for msg in messages:            
                if isinstance(msg, HumanMessage):
                    conversation.append({
                        "role": "user",
                        "content": msg.content + "\n" + prompt
                    })
            
                elif isinstance(msg, AIMessage):
                    conversation.append({
                        "role": "assistant",
                        "content": msg.content
                    })
            
                elif isinstance(msg, SystemMessage):
                    conversation.append({
                        "role": "system",
                        "content": msg.content
                    })
            
                elif isinstance(msg, ToolMessage):
                    conversation.append({
                        "role": "tool",
                        "content": msg.content
                    })
            return conversation ,[]
        else:
            conversation = []

            all_images = []

            for msg in messages:

                if isinstance(msg, HumanMessage):

                    text, images = self.extract_content(msg.content)

                    content = []

                    for img in images:
                        content.append({
                            "type": "image",
                            "image": img
                        })
                        all_images.append(img)

                    content.append({
                        "type": "text",
                        "text": text + "\n" + prompt
                    })

                    conversation.append({
                        "role": "user",
                        "content": content
                    })

                elif isinstance(msg, AIMessage):

                    conversation.append({
                        "role":"assistant",
                        "content":[
                            {
                                "type":"text",
                                "text":self.to_text(msg.content)
                            }
                        ]
                    })

                elif isinstance(msg, ToolMessage):

                    text, images = self.extract_content(msg.content)
                    
                    content = []
                    
                    for img in images:
                        content.append({
                            "type": "image",
                            "image": img
                        })
                        all_images.append(img)
                    
                    content.append({
                        "type": "text",
                        "text": text 
                    })
                    
                    conversation.append({
                        "role": "user",
                        "content": content
                    })
                elif isinstance(msg, SystemMessage):

                    conversation.append({
                        "role":"system",
                        "content":[
                            {
                                "type":"text",
                                "text":msg.content
                            }
                        ]
                    })

            return conversation, all_images
    def _generate(self, messages,prompts="", stop=None, run_manager=None, **kwargs):
        # print("message",messages)
        conversation, images = self._build_prompt(messages, prompts)
        print('image aaya hai .....')
        chat = self._processor.apply_chat_template(
            conversation,
            add_generation_prompt=True,
            tokenize=False,enable_thinking=True
        )

        if images:
            print('image walal processor')
            inputs = self._processor(
                text=chat,
                images=images,
                return_tensors="pt"
            )
        else:
            print('text walal processor')
            inputs = self._processor(
                text=chat,
                return_tensors="pt"
            )
        # print(inputs.keys())
        out = self._generate_sync(inputs)

        text = self._processor.decode(out[0], skip_special_tokens=True)
        output = text.strip()

        # ----- your existing parsing code -----
        cleaned_output = output.split("</think>")[-1].strip()

        if cleaned_output.startswith("```"):
            cleaned_output = cleaned_output.strip()
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output[7:].strip()
            elif cleaned_output.startswith("```"):
                cleaned_output = cleaned_output[3:].strip()

            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3].strip()

        if "\nassistant\n" in cleaned_output:
            cleaned_output = cleaned_output.rsplit("\nassistant\n", 1)[-1].strip()
        print("cleaned_output: ",cleaned_output)
        try:
            obj=json.loads(cleaned_output)
            # for tool calls
            if obj is not None and  "tool_calls" in obj and obj['tool_calls']:
                new_li=[]
                for tool in obj['tool_calls']:
                    new_li.append({'name': tool['name'], 'args': tool.get('args', {}), 'id': str(uuid.uuid4())})
                msg = AIMessage(content="", tool_calls=new_li)
            # for actions 
            elif obj is not None and "actions" in obj :
                msg=AIMessage(content="",actions=obj['actions'])
            # for anything else 
            else:
                msg=AIMessage(content=cleaned_output)
                    
        except Exception as e:
            msg=AIMessage(content=cleaned_output)

        return ChatResult(
            generations=[
                ChatGeneration(message=msg)
            ]
        )
    async def _agenerate(
            self,
            messages,
            stop=None,
            run_manager=None,
            **kwargs,
        ):
        prompts = kwargs.get("browser_prompt", "")
        return await asyncio.to_thread(
            self._generate,
            messages,
            prompts,
            stop,
            run_manager,
            **kwargs,
        )
    # async def execute_page_actions(self,page,actions):
    #     result=[]
    #     for action in actions:
    #         data=await execute_action(page,action,self.state)
    #         result.append(data)
    #         if data.get('page',""):
    #             break
    #     return result


    