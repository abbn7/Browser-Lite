import asyncio,json,os
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 base=os.getenv('TEST_BASE_URL','http://127.0.0.1:8765')
 password=os.getenv('TEST_APP_PASSWORD','local-testing-password')
 output=Path(os.getenv('TEST_OUTPUT_DIR','/workspace/scratch'));output.mkdir(parents=True,exist_ok=True)
 async with async_playwright() as p:
  b=await p.chromium.launch()
  page=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
  errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(base)
  await page.locator('#password').fill(password)
  await page.locator('#loginForm button').click()
  await page.wait_for_function("() => !document.getElementById('loginDialog').open")
  await page.screenshot(path=str(output/'browser-lite-mobile.png'),full_page=True)
  await page.locator('#url').fill('https://example.com')
  await page.locator('#open').click()
  await page.locator('#screen').wait_for(state='visible',timeout=45000)
  await page.wait_for_function("() => document.getElementById('screen').naturalWidth > 0")
  await page.screenshot(path=str(output/'browser-lite-live.png'),full_page=True)
  for width in [360,430]:
   await page.set_viewport_size({'width':width,'height':844})
   assert not await page.evaluate('document.documentElement.scrollWidth > innerWidth')
  print(json.dumps({'console_errors':errors,'horizontal_overflow':await page.evaluate('document.documentElement.scrollWidth > innerWidth'),'frame_width':await page.locator('#screen').evaluate('(e)=>e.naturalWidth')}))
  await b.close()
asyncio.run(main())
