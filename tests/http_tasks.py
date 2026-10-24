import time,json,os,httpx
base=os.getenv('TEST_BASE_URL','http://127.0.0.1:8767')
with httpx.Client(base_url=base,trust_env=False,timeout=90) as c:
 for _ in range(30):
  try:
   if c.get('/healthz').status_code==200:break
  except httpx.HTTPError:pass
  time.sleep(1)
 r=c.post('/api/login',json={'password':os.getenv('TEST_APP_PASSWORD','container-testing-password')},headers={'Origin':base});r.raise_for_status()
 h={'Origin':base,'X-CSRF-Token':r.json()['csrf']}
 results=[]
 for i in range(3):
  r=c.post('/api/tasks',json={'url':'https://example.com','instruction':'Read and scroll the example page'},headers=h)
  assert r.status_code==200,r.text
  duplicate=c.post('/api/tasks',json={'url':'https://example.com','instruction':'second'},headers=h)
  assert duplicate.status_code==409,duplicate.text
  deadline=time.monotonic()+120
  while time.monotonic()<deadline:
   state=c.get('/api/state').json()
   if not state['busy']:break
   time.sleep(.5)
  assert state['task']['status']=='completed',state
  results.append({'status':state['task']['status'],'steps':state['task']['steps']})
 print(json.dumps({'http_tasks':results,'parallel_task_rejected':True}))
