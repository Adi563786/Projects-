from langchain_core.tools import tool
import asyncio
from State import WebState
from io import BytesIO
from PIL import Image

@tool
async def get_screenshot(page):
    """recieve a playwright object name as page and output a PIL image object of current page """
    img_bytes= await page.screenshot(type='png')
    img=Image.open(BytesIO(img_bytes))
    return img.resize((720,720) , Image.Resampling.LANCZOS)
@tool
async def scroll_mouse(pixels:int,page):
    """recieve coordinates how muc pixel user want tos scroll ,positive x means scroll down and negative x means scroll up and return status as string"""
    await page.mouse.wheel(0,pixels)
    return f' scrolled {"up" if pixels<0 else "down"} by {pixels} pixels'

def get_tools():
    dic={
        get_screenshot.name:get_screenshot,
        scroll_mouse.name:scroll_mouse
    }
    return dic ,[get_screenshot,scroll_mouse]



