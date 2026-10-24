import asyncio,json,os
from pathlib import Path
from playwright.async_api import async_playwright
BASE=os.getenv('TEST_BASE_URL','http://127.0.0.1:8780')
PASSWORD=os.getenv('TEST_APP_PASSWORD','workspace-testing-password')
OUTPUT=Path(os.getenv('TEST_OUTPUT_DIR','/workspace/scratch'));OUTPUT.mkdir(exist_ok=True,parents=True)
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch();page=await b.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(BASE);await page.locator('#password').fill(PASSWORD);await page.locator('#loginForm button').click();await page.locator('#loginDialog').wait_for(state='hidden');await page.locator('#toast').wait_for(state='hidden')
  await page.screenshot(path=str(OUTPUT/'workspace-mobile.png'))
  await page.locator('#url').fill('https://example.com');await page.locator('#open').click();await page.locator('#screen').wait_for(state='visible',timeout=45000)
  assert await page.locator('#screen').evaluate('(e)=>e.naturalWidth')==1280
  assert await page.locator('#screen').evaluate('(e)=>e.naturalHeight')==800
  await page.locator('#zoomIn').click();assert await page.locator('#zoomLabel').inner_text()=='150%';await page.locator('#zoomOut').click()
  await page.locator('#activityOpen').click();assert await page.locator('#activityPanel').evaluate('(e)=>e.classList.contains("open")');await page.locator('#activityClose').click()
  await page.locator('#settingsOpen').click();await page.locator('#proxyUrl').fill('socks5://proxy.example:1080');await page.locator('#proxyUsername').fill('test');await page.locator('#proxyPassword').fill('private-test-password');await page.locator('#proxySave').click();await page.wait_for_function('() => document.getElementById("proxyResult").textContent.includes("اتحفظت")');assert await page.locator('#proxyPassword').input_value()=='';await page.locator('#settingsClose').click()
  for width in [360,390,430,1280]:
   await page.set_viewport_size({'width':width,'height':844});assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth');assert await page.locator('#form').evaluate('(e)=>e.getBoundingClientRect().bottom')<844
  await page.screenshot(path=str(OUTPUT/'workspace-desktop.png'))
  assert not errors,errors
  print(json.dumps({'widths':[360,390,430,1280],'desktop_frame':[1280,800],'proxy_settings_saved':True,'js_errors':errors}))
  await b.close()
asyncio.run(main())
