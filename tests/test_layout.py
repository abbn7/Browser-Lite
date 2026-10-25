import asyncio,tempfile
import pytest
from engine import Engine
from store import Store

def test_desktop_layout_is_bounded_and_defers_while_running():
    async def run():
        with tempfile.TemporaryDirectory() as d:
            e=Engine(Store(d))
            assert await e.layout(5000)=={'width':1280,'height':2200}
            e.job=asyncio.create_task(asyncio.sleep(60))
            with pytest.raises(ValueError):await e.layout(1000)
            assert e.viewport['height']==2200
            await e.pause()
            assert await e.layout(1200)=={'width':1280,'height':1200}
    asyncio.run(run())

def test_start_does_not_add_boilerplate_assistant_messages():
    async def run():
        with tempfile.TemporaryDirectory() as d:
            e=Engine(Store(d));e.llm=lambda:object()
            async def deferred(first=False):await asyncio.sleep(60)
            e.run=deferred
            await e.start('','ابحث عن الوثائق')
            assert [m['role'] for m in e.task['messages']]==['user']
            await e.pause(cancel=True)
    asyncio.run(run())

def test_small_container_uses_a_smaller_desktop_capture(monkeypatch):
    import engine as runtime
    monkeypatch.setattr(runtime,'container_memory',lambda:(100*1024**2,512*1024**2))
    async def run():
        with tempfile.TemporaryDirectory() as d:
            e=Engine(Store(d))
            assert await e.layout(2200)=={'width':1280,'height':1600}
    asyncio.run(run())

def test_browser_not_exposed_until_startup_finishes(monkeypatch):
    import engine as runtime
    class FakeBrowser:
        def __init__(self,**kwargs):pass
        async def start(self):
            entered.set();await release.wait()
        async def kill(self):pass
    async def run():
        nonlocal entered,release
        entered=asyncio.Event();release=asyncio.Event()
        with tempfile.TemporaryDirectory() as d:
            e=Engine(Store(d));e.proxy_port=9000
            async def metrics():pass
            e.ensure_metrics=metrics
            job=asyncio.create_task(e.ensure_browser())
            await entered.wait();assert e.browser is None
            release.set();await job
            assert isinstance(e.browser,FakeBrowser)
            await e.close_browser()
    entered=release=None
    monkeypatch.setattr(runtime,'Browser',FakeBrowser)
    asyncio.run(run())

@pytest.mark.parametrize('name,params',[
    ('find_elements',{'selector':'h1'}),
    ('search_page',{'pattern':'title'}),
    ('dropdown_options',{'index':1}),
])
def test_read_only_page_tools_do_not_wait_for_mutation_approval(monkeypatch,name,params):
    from engine import SafeTools
    from browser_use import Tools
    from browser_use.agent.views import ActionResult
    async def run():
        with tempfile.TemporaryDirectory() as d:
            e=Engine(Store(d));e.task={'id':'read','allow_actions':False,'status':'running'}
            tools=SafeTools(e);Action=tools.registry.create_action_model();calls=[]
            async def act(self,action,*args,**kwargs):
                calls.append(action);return ActionResult(extracted_content='page data')
            monkeypatch.setattr(Tools,'act',act)
            await asyncio.wait_for(tools.act(Action(**{name:params}),None),1)
            assert len(calls)==1 and e.task['status']=='running'
    asyncio.run(run())
