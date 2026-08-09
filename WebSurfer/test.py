from playwright.async_api import async_playwright 
from utils import get_page_details
import asyncio
from collections import defaultdict
async def main(url):
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=False)
        context=await browser.new_context()
        page=await context.new_page()

        await page.goto(url)
        elements=await get_page_details(page)
        print(elements)

        target = page.locator(f'[data-agent-id="{440}"]')
        text=await target.inner_text()
        print(text)
        snap=await target.aria_snapshot(timeout=3000,mode='ai')
        print(type(snap),snap)
        await target.screenshot(
            path="abc.png",type='jpeg',quality=90,animations='disabled'
        )
        return 
asyncio.run(main("https://en.wikipedia.org/wiki/Diana_Ross"))

