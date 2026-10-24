import subprocess,time,json
values=[]
for _ in range(120):
 try:
  raw=subprocess.check_output(['docker','exec','browser-lite-e2e','python','-c',"from resources import container_memory;print(container_memory()[0])"],stderr=subprocess.DEVNULL,text=True)
  values.append(int(raw.strip()))
 except Exception:pass
 time.sleep(1)
print(json.dumps({'samples':len(values),'peak_working_set_mib':round(max(values)/1024**2,1) if values else None}))
