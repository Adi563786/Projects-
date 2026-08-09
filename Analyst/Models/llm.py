from xml.parsers.expat import model

from langchain_groq  import ChatGroq
import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import json
import re

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
nvidia_api_key = os.getenv("NVIDIA")
model_name="nvidia/llama-3.1-nemotron-70b-instruct"
grok_model_name="llama-3.3-70b-versatile"

class LLM:
    def __init__(self, model_name=grok_model_name, temperature=0.3, max_tokens=4196, api_key=groq_api_key):
        
        self.model = ChatGroq(model=model_name, temperature=temperature, max_tokens=max_tokens, api_key=api_key)
       
        # self.model = ChatNVIDIA(model=model_name, temperature=temperature, max_tokens=max_tokens, api_key=nvidia_api_key)
    def invoke(self, prompt):
        # Call the LLM with the prompt and parse the output into PlanModel
        response = self.model.invoke(prompt)
        return response
    def structured_invoke(self, prompt, response_model):
        try:
            response = self.model.with_structured_output(response_model, method="json_mode").invoke(prompt)
            return response
        except Exception as e:
            # Fallback: try to extract and fix JSON if structured output fails
            print(f"Structured output failed: {str(e)}")
            print("Attempting fallback JSON extraction...")
            plain_response = self.model.invoke(prompt)
            response_text = plain_response.content if hasattr(plain_response, 'content') else str(plain_response)
            
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    # Fix unescaped quotes in SQL strings
                    json_str = self._fix_json_escaping(json_str)
                    data = json.loads(json_str)
                    return response_model(**data)
                except Exception as inner_e:
                    print(f"Fallback also failed: {str(inner_e)}")
                    raise e
            raise e
    
    @staticmethod
    def _fix_json_escaping(json_str):
        """Attempt to fix common JSON escaping issues in SQL queries"""
        try:
            # First try to load as-is
            return json.loads(json_str)
        except json.JSONDecodeError:
            # If it fails, the JSON might have unescaped quotes in string values
            # This is a simple heuristic fix - be careful with complex cases
            import json
            pass
        return json_str

# class LLM:
#     def __init__(self,model_name=grok_model_name,temperature=0.3,max_tokens=4196,api_key=groq_api_key):
#         self.model=ChatGroq(model=model_name,temperature=temperature,max_tokens=max_tokens,api_key=api_key)
#         #self.model=ChatNVIDIA(model=model_name,temperature=temperature,max_tokens=max_tokens,api_key=nvidia_api_key)

#     def invoke(self,prompt):
#         # Call the LLM with the prompt and parse the output into PlanModel
#         response=self.model.invoke(prompt)
#         return response
    
#     def structured_invoke(self, prompt, response_model):
#         try:
#             response = self.model.with_structured_output(response_model, method="json_mode").invoke(prompt)
#             return response
#         except Exception as e:
#             # Fallback: try to extract and fix JSON if structured output fails
#             print(f"Structured output failed: {str(e)}")
#             print("Attempting fallback JSON extraction...")
#             plain_response = self.model.invoke(prompt)
#             response_text = plain_response.content if hasattr(plain_response, 'content') else str(plain_response)
            
#             # Try to extract JSON from response
#             json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
#             if json_match:
#                 try:
#                     json_str = json_match.group(0)
#                     # Fix unescaped quotes in SQL strings
#                     json_str = self._fix_json_escaping(json_str)
#                     data = json.loads(json_str)
#                     return response_model(**data)
#                 except Exception as inner_e:
#                     print(f"Fallback also failed: {str(inner_e)}")
#                     raise e
#             raise e
    
#     @staticmethod
#     def _fix_json_escaping(json_str):
#         """Attempt to fix common JSON escaping issues in SQL queries"""
#         try:
#             # First try to load as-is
#             return json.loads(json_str)
#         except json.JSONDecodeError:
#             # If it fails, the JSON might have unescaped quotes in string values
#             # This is a simple heuristic fix - be careful with complex cases
#             import json
#             pass
#         return json_str

# class miniLLM:
    
#     def __init__(self,model_name="qwen/qwen3.6-27b",temperature=0.3,max_tokens=8191,api_key=groq_api_key):
#         #self.model=ChatNVIDIA(model=model_name,temperature=temperature,max_tokens=max_tokens,api_key=nvidia_api_key)
#         self.model=ChatGroq(model=model_name,temperature=temperature,max_tokens=max_tokens,api_key=api_key)

#     def invoke(self,prompt):
#         # Call the LLM with the prompt and parse the output into PlanModel
#         response=self.model.invoke(prompt)
#         return response
    
#     def structured_invoke(self, prompt, response_model):
#         try:
#             response = self.model.with_structured_output(response_model, method='json_mode').invoke(prompt)
#             return response
#         except Exception as e:
#             # Fallback: try to extract and fix JSON if structured output fails
#             print(f"Structured output failed: {str(e)}")
#             print("Attempting fallback JSON extraction...")
#             plain_response = self.model.invoke(prompt)
#             response_text = plain_response.content if hasattr(plain_response, 'content') else str(plain_response)
            
#             # Try to extract JSON from response
#             json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
#             if json_match:
#                 try:
#                     json_str = json_match.group(0)
#                     data = json.loads(json_str)
#                     return response_model(**data)
#                 except Exception as inner_e:
#                     print(f"Fallback also failed: {str(inner_e)}")
#                     raise e
#             raise e
