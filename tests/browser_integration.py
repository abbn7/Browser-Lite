"""Real Chromium and Browser-use; deterministic model, no paid inference."""
import os,asyncio,tempfile,json
os.environ['ANONYMIZED_TELEMETRY']='false'
os.environ['BROWSER_USE_LOGGING_LEVEL']='error'
from store import Store
from engine import Engine
from browser_use.llm.views import ChatInvokeCompletion
class ScriptedModel:
    model='test-scripted';provider='test';name='test-scripted';model_name='test-scripted';_verified_api_keys=True
    calls=0
    async def ainvoke(self,messages,output_format=None,**kw):
        self.calls+=1
        payload={'evaluation_previous_goal':'Page inspected','memory':'Opened test page','next_goal':'Finish test','action':[{'done':{'text':'Browser integration passed','success':True}}]}
        return ChatInvokeCompletion(completion=output_format.model_validate(payload),usage=None)
async def main():
    with tempfile.TemporaryDirectory() as d:
        e=Engine(Store(d));model=ScriptedModel();e.llm=lambda:model
        try:
            await e.start('https://example.com','Read the page and finish')
            await asyncio.wait_for(e.job,90)
            assert e.task['status']=='completed',e.task
            shot=await e.snapshot();assert shot[:2]==b'\xff\xd8'
            # Verify real CDP typing, Unicode, click and scroll on a controlled page.
            session=await e.browser.get_or_create_cdp_session()
            await session.cdp_client.send.Runtime.evaluate(params={'expression':"document.body.innerHTML='<input id=field style=\"position:fixed;left:0;top:0;width:300px;height:60px\">';document.getElementById('field').focus()"},session_id=session.session_id)
            await e.input({'kind':'text','text':'اختبار Browser Lite'})
            r=await session.cdp_client.send.Runtime.evaluate(params={'expression':"document.getElementById('field').value",'returnByValue':True},session_id=session.session_id)
            assert r['result']['value']=='اختبار Browser Lite'
            await e.input({'kind':'key','key':'Backspace'})
            await e.input({'kind':'scroll','delta':100})
            await e.input({'kind':'click','x':100,'y':20})
            print(json.dumps({'agent_status':e.task['status'],'model_calls':model.calls,'jpeg_bytes':len(shot),'unicode_input':True}))
        finally:await e.close()
asyncio.run(main())
