"""Geometry, real CDP click and UI regression. Run ui_minimal_app.py first.
The task timeline below is an explicitly synthetic UI fixture, not model inference.
"""
import asyncio,json,time,os
from pathlib import Path
from playwright.async_api import async_playwright
BASE=os.getenv('TEST_BASE_URL','http://127.0.0.1:8785');PASSWORD=os.getenv('TEST_APP_PASSWORD','minimal-testing-password')
OUT=Path(os.getenv('TEST_OUTPUT_DIR','/workspace/scratch/minimal-tests'));OUT.mkdir(parents=True,exist_ok=True)
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch();page=await b.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
  errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
  await page.goto(BASE);await page.locator('#password').fill(PASSWORD);await page.locator('#loginForm button').click();await page.locator('#loginDialog').wait_for(state='hidden');await page.locator('#toast').wait_for(state='hidden')
  await page.locator('#url').fill('https://example.com');await page.locator('#open').click();await page.locator('#screen').wait_for(state='visible',timeout=45000)
  await page.wait_for_function('() => document.getElementById("screen").naturalHeight>=2000')
  for width in [360,390,430,1280]:
   await page.set_viewport_size({'width':width,'height':844});await page.wait_for_timeout(500)
   assert not await page.evaluate('document.documentElement.scrollWidth>innerWidth')
   rect=await page.locator('#screen').bounding_box();assert abs(rect['x'])<1 and abs(rect['width']-width)<1
   dimensions=await page.locator('#screen').evaluate('(e)=>[e.naturalWidth,e.naturalHeight]');assert dimensions[0]==1280
   assert abs(rect['width']/rect['height']-dimensions[0]/dimensions[1])<.002
   assert await page.locator('#form').evaluate('(e)=>e.getBoundingClientRect().bottom')<=844
  await page.set_viewport_size({'width':390,'height':844});await page.wait_for_timeout(600)
  # Known target at native coordinates (640,300): verify actual browser hit.
  await page.evaluate("async()=>{const r=await fetch('/__test/target',{method:'POST',headers:{'X-CSRF-Token':csrf}});if(!r.ok)throw Error('fixture failed')}")
  await page.wait_for_timeout(1100)
  rect=await page.locator('#screen').bounding_box();height=await page.locator('#screen').evaluate('(e)=>e.naturalHeight')
  await page.mouse.click(rect['x']+rect['width']*640/1280,rect['y']+rect['height']*300/height)
  await page.wait_for_timeout(300)
  metrics=await page.evaluate("async()=>await(await fetch('/__test/metrics')).json()")
  assert metrics['hits']==1 and metrics['innerWidth']==1280 and metrics['screenWidth']==1280 and metrics['dpr']==1,metrics
  await page.locator('#toolsOpen').click();await page.locator('#zoomIn').click();await page.wait_for_timeout(150)
  rect=await page.locator('#screen').bounding_box();height=await page.locator('#screen').evaluate('(e)=>e.naturalHeight')
  await page.mouse.click(rect['x']+rect['width']*640/1280,rect['y']+rect['height']*300/height)
  await page.wait_for_timeout(300)
  metrics=await page.evaluate("async()=>await(await fetch('/__test/metrics')).json()")
  assert metrics['hits']==2,metrics
  # Synthetic timeline proves no fabricated per-second events or repeated bubbles.
  await page.evaluate('() => {stream.onmessage=null;stream.close();}')
  now=time.time()
  state={'browser_ready':True,'busy':True,'viewport':{'width':1280,'height':2200},'proxy':{'enabled':False},'files':[],'task':{'id':'ui-fixture','status':'running','steps':1,'url':'https://example.com','message':'انتظار رد الموديل لتحديد الفعل التالي','messages':[{'id':'user-fixture','role':'user','content':'راجع الصفحة.'}],'events':[{'seq':1,'kind':'model','title':'انتظار رد الموديل لتحديد الفعل التالي','time':now}]}}
  await page.evaluate('(s)=>render(s)',state)
  bubble=page.locator('.chat-message').first;await bubble.evaluate('(e)=>e.dataset.identity="retained"')
  first=await page.locator('#eventElapsed').inner_text();await page.wait_for_function('(before)=>document.getElementById("eventElapsed").textContent!==before',arg=first,timeout=4000)
  assert await page.locator('#eventCount').inner_text()=='1'
  state['task']['messages'].append({'id':'assistant-fixture','role':'assistant','content':'تمام، دي النتيجة.'});await page.evaluate('(s)=>render(s)',state)
  assert await bubble.evaluate('(e)=>e.dataset.identity')=='retained'
  assert await page.locator('.chat-message').count()==2
  await page.locator('.edit-message').click();assert await page.locator('#instruction').input_value()=='راجع الصفحة.';await page.locator('#cancelEdit').click()
  await page.locator('#activityOpen').click();assert await page.locator('#activityPanel').evaluate('(e)=>e.open');await page.locator('#activityClose').click()
  assert await page.locator('#start').get_attribute('aria-label')=='إيقاف مؤقت'
  await page.locator('#instruction').fill('كمّل');assert await page.locator('#start').get_attribute('aria-label')=='إرسال'
  await page.locator('#instruction').fill('');assert await page.locator('#start').get_attribute('aria-label')=='إيقاف مؤقت'
  async with page.expect_response(lambda r:'/api/control/pause' in r.url and r.request.method=='POST') as pause:
   await page.locator('#start').click()
  assert (await pause.value).status==200
  await page.wait_for_function('() => document.getElementById("start").disabled')
  await page.locator('#settingsOpen').click();await page.locator('#proxyUrl').fill('socks5://proxy.example:1080');await page.locator('#proxyPassword').fill('test-password');await page.locator('#proxySave').click();await page.wait_for_function('() => document.getElementById("proxyResult").textContent.includes("تم الحفظ")');assert await page.locator('#proxyPassword').input_value()=='';await page.locator('#settingsClose').click()
  assert not errors,errors
  print(json.dumps({'widths':[360,390,430,1280],'pixel_mapping_hits':metrics['hits'],'clock_ticks_without_new_events':True,'keyed_chat':True,'send_pause_control':True,'proxy_settings':True,'js_errors':errors}))
  await b.close()
asyncio.run(main())
