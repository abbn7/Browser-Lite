import asyncio, os, tempfile
os.environ['APP_PASSWORD']='unit-testing-password'
os.environ['DATA_DIR']=tempfile.mkdtemp()
os.environ['ANONYMIZED_TELEMETRY']='false'
from fastapi.testclient import TestClient
from app import app, engine
from network import validate_url,public_address
from store import Store

def login(c):
    response=c.post('/api/login',json={'password':'unit-testing-password'},headers={'Origin':'http://testserver'})
    assert response.status_code==200
    return {'Origin':'http://testserver','X-CSRF-Token':response.json()['csrf']}

def test_auth_and_csrf():
    with TestClient(app) as c:
        assert c.get('/api/state').status_code==401
        assert c.post('/api/login',json={'password':'unit-testing-password'},headers={'Origin':'https://evil.test'}).status_code==403
        headers=login(c)
        assert c.get('/api/state').status_code==200
        assert c.post('/api/control/pause').status_code==403
        assert c.post('/api/control/pause',headers=headers).status_code==200
        assert 'HttpOnly' in c.cookies.jar._cookies['testserver.local']['/']['browser_lite_session']._rest
        assert c.post('/api/logout',headers=headers).status_code==200
        assert c.get('/api/state').status_code==401

def test_network_blocks_private():
    for url in ['http://127.0.0.1','http://169.254.169.254','http://[::1]','http://localhost','file:///etc/passwd','http://user:pass@example.com','https://example.com:22']:
        try:asyncio.run(validate_url(url))
        except (ValueError,OSError):pass
        else:raise AssertionError(url)

def test_persistence_and_recovery():
    from engine import Engine
    with tempfile.TemporaryDirectory() as d:
        store=Store(d)
        store.save({'id':'1','status':'running','steps':4,'summary':'progress'})
        restored=Engine(store)
        assert restored.task['status']=='paused'
        assert restored.task['steps']==4

def test_no_model_secret_exposure():
    os.environ['LLM_API_KEY']='test-secret-do-not-return'
    with TestClient(app) as c:
        login(c)
        assert 'test-secret' not in c.get('/api/session').text
        assert c.get('/api/files/absent').status_code==404
    os.environ.pop('LLM_API_KEY')

def test_safe_tools_exclude_code():
    from engine import SafeTools
    names=SafeTools(engine).registry.registry.actions
    for name in ['evaluate','upload_file','write_file','read_file','replace_file']:
        assert name not in names
    assert 'ask_owner' in names

def test_single_task_and_cancellation():
    async def scenario():
        with tempfile.TemporaryDirectory() as d:
            from engine import Engine
            e=Engine(Store(d))
            e.job=asyncio.create_task(asyncio.sleep(60))
            try:
                await e.start('https://example.com','test')
            except ValueError:pass
            else:raise AssertionError('accepted a second task')
            e.task={'id':'t','status':'running'}
            await e.pause(cancel=True)
            assert e.job.done() and e.task['status']=='cancelled'
    asyncio.run(scenario())

def test_mutation_requires_approval(monkeypatch):
    from engine import SafeTools,Engine
    from browser_use import Tools
    from browser_use.agent.views import ActionResult
    async def scenario():
        with tempfile.TemporaryDirectory() as d:
            e=Engine(Store(d));e.task={'id':'gate','status':'running','allow_actions':False}
            tools=SafeTools(e)
            Action=tools.registry.create_action_model()
            calls=[]
            async def fake_act(self,action,*args,**kw):
                calls.append(action);return ActionResult(extracted_content='ok')
            monkeypatch.setattr(Tools,'act',fake_act)
            task=asyncio.create_task(tools.act(Action(input={'index':1,'text':'test'}),None))
            await asyncio.sleep(.02)
            assert e.task['status']=='waiting_approval' and not calls
            await e.approve();await task
            assert len(calls)==1
    asyncio.run(scenario())

def test_file_navigation_rejected():
    from engine import SafeTools
    async def scenario():
        tools=SafeTools(engine)
        Action=tools.registry.create_action_model()
        result=await tools.act(Action(navigate={'url':'file:///etc/passwd','new_tab':False}),None)
        assert result.error
    asyncio.run(scenario())
