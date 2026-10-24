"""Run with: docker exec ... python /tmp/container_smoke.py
Uses the actual app process via HTTP and a separate Browser-use process only after
closing the app browser. A deterministic model tests orchestration, NOT model intelligence.
"""
import asyncio,json,os,tempfile,time,sys
sys.path.insert(0,'/app')
import httpx
from store import Store
from engine import Engine
from browser_use.llm.views import ChatInvokeCompletion
class Model:
    model='scripted-test';name='scripted-test';model_name='scripted-test';provider='test';_verified_api_keys=True
    def __init__(self):self.calls=0
    async def ainvoke(self,messages,output_format=None,**kwargs):
        self.calls+=1
        actions=[{'scroll':{'down':True,'pages':0.5}},{'done':{'text':'Container task passed','success':True}}]
        body={'evaluation_previous_goal':'Verified','memory':'Read example page','next_goal':'Continue test','action':[actions[min(self.calls-1,1)]]}
        return ChatInvokeCompletion(completion=output_format.model_validate(body),usage=None)
async def main():
    os.environ['BROWSER_UPSTREAM_PROXY']=os.environ.get('HTTPS_PROXY','')
    with tempfile.TemporaryDirectory() as d:
        e=Engine(Store(d));results=[];peaks=[]
        try:
            for i in range(3):
                model=Model();e.llm=lambda:model
                await e.start('https://example.com','Read and scroll the example page')
                while not e.job.done():
                    try:
                        from resources import container_memory
                        used,limit=container_memory();peaks.append(used or 0)
                    except Exception:pass
                    await asyncio.sleep(.3)
                await e.job
                results.append({'status':e.task['status'],'calls':model.calls,'steps':e.task['steps']})
                assert e.task['status']=='completed',e.task
            print(json.dumps({'tasks':results,'peak_working_set_mib':round(max(peaks)/1024**2,1)}))
        finally:await e.close()
if __name__=='__main__':asyncio.run(main())
