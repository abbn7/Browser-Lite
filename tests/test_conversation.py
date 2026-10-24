import asyncio,tempfile
from engine import Engine,SafeTools
from store import Store
from browser_use import Tools
from browser_use.agent.views import ActionResult

def test_edit_interrupts_task_and_preserves_history():
    async def run():
        with tempfile.TemporaryDirectory() as d:
            e=Engine(Store(d));e.task={'id':'chat','status':'running','instruction':'old','steps':3,'url':'https://example.com'}
            e.chat('user','old');mid=e.task['messages'][0]['id'];e.chat('assistant','old answer')
            e.job=asyncio.create_task(asyncio.sleep(60));oldjob=e.job
            e.llm=lambda:object()
            async def resumed():await asyncio.sleep(60)
            e.run=resumed
            await e.message('new direction',mid)
            assert oldjob.cancelled()
            assert e.task['instruction']=='new direction'
            assert e.task['messages'][1]['outdated']
            assert e.task['steps']==3 and e.task['events']
            restored=Engine(Store(d));assert restored.task['messages'][0]['content']=='new direction'
            await e.pause(cancel=True)
    asyncio.run(run())

def test_action_events_do_not_log_typed_values(monkeypatch):
    async def run():
        with tempfile.TemporaryDirectory() as d:
            e=Engine(Store(d));e.task={'id':'actions','allow_actions':True,'status':'running'}
            tools=SafeTools(e);Action=tools.registry.create_action_model()
            async def act(self,action,*args,**kwargs):return ActionResult(extracted_content='ok')
            monkeypatch.setattr(Tools,'act',act)
            await tools.act(Action(input={'index':1,'text':'private-value'}),None)
            assert [x['kind'] for x in e.task['events']]==['action','action_done']
            assert 'private-value' not in str(e.task['events'])
    asyncio.run(run())

def test_conversation_can_start_without_a_link():
    async def run():
        with tempfile.TemporaryDirectory() as d:
            e=Engine(Store(d));e.llm=lambda:object()
            async def deferred(first=False):await asyncio.sleep(60)
            e.run=deferred
            await e.start('','محتاج مساعدتك في البحث')
            assert e.task['url']=='' and e.task['messages'][0]['role']=='user'
            await e.pause(cancel=True)
    asyncio.run(run())
