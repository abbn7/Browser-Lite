import asyncio, base64, hashlib, hmac, json, os, secrets, shutil, time
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit
os.environ.setdefault('ANONYMIZED_TELEMETRY','false')
os.environ.setdefault('BROWSER_USE_LOGGING_LEVEL','error')
from fastapi import FastAPI, Request, Response, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from store import Store
from engine import Engine

ROOT=Path(__file__).parent
store=Store(os.getenv('DATA_DIR',str(ROOT/'data')))
engine=Engine(store)
sessions={}
attempts={}

@asynccontextmanager
async def lifespan(app):
    if len(os.getenv('APP_PASSWORD',''))<12:
        raise RuntimeError('Set APP_PASSWORD to at least 12 characters')
    async def maintenance():
        while True:
            await asyncio.sleep(30)
            active=engine.job and not engine.job.done()
            if not active and time.monotonic()-engine.last_used>120:
                await engine.close_browser()
            downloads=store.root/'downloads'
            if downloads.exists():
                files=sorted((p for p in downloads.iterdir() if p.is_file()),key=lambda p:p.stat().st_mtime)
                total=sum(p.stat().st_size for p in files)
                for p in files:
                    size=p.stat().st_size
                    if time.time()-p.stat().st_mtime>86400 or size>10*1024**2 or total>50*1024**2:
                        p.unlink(missing_ok=True);total-=size
    task=asyncio.create_task(maintenance())
    yield
    task.cancel()
    await asyncio.gather(task,return_exceptions=True)
    await engine.close()

app=FastAPI(lifespan=lifespan,docs_url=None,redoc_url=None,openapi_url=None)

def same_origin(request):
    origin=request.headers.get('origin')
    if not origin:return False
    p=urlsplit(origin)
    return p.scheme in ('http','https') and p.netloc==request.headers.get('host')

def authenticate(request):
    token=request.cookies.get('browser_lite_session','')
    entry=sessions.get(hashlib.sha256(token.encode()).hexdigest())
    if not entry or entry['expires']<time.time():raise HTTPException(401,'سجّل الدخول أولًا')
    return entry

async def owner(request:Request):
    entry=authenticate(request)
    if request.method not in ('GET','HEAD'):
        if not same_origin(request) or not hmac.compare_digest(request.headers.get('x-csrf-token',''),entry['csrf']):
            raise HTTPException(403,'Invalid origin or CSRF token')
    return entry

@app.middleware('http')
async def headers(request,call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
    response.headers['Cache-Control']='no-store' if request.url.path.startswith('/api') else 'no-cache'
    return response

class Login(BaseModel):password:str=Field(max_length=512)
@app.post('/api/login')
async def login(body:Login,request:Request,response:Response):
    if not same_origin(request):raise HTTPException(403,'Invalid origin')
    ip=request.client.host
    recent=[t for t in attempts.get(ip,[]) if time.time()-t<300]
    attempts[ip]=recent
    if len(recent)>=10:raise HTTPException(429,'حاول بعد خمس دقائق')
    expected=os.getenv('APP_PASSWORD','')
    if len(expected)<12 or not secrets.compare_digest(body.password,expected):
        recent.append(time.time());raise HTTPException(401,'كلمة المرور غير صحيحة')
    attempts.pop(ip,None)
    token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(24)
    # Bound session storage and expire old sessions.
    for k,v in list(sessions.items()):
        if v['expires']<time.time():sessions.pop(k,None)
    if len(sessions)>=100:sessions.clear()
    sessions[hashlib.sha256(token.encode()).hexdigest()]={'csrf':csrf,'expires':time.time()+86400}
    secure=request.url.scheme=='https' or request.headers.get('x-forwarded-proto')=='https'
    response.set_cookie('browser_lite_session',token,httponly=True,secure=secure,samesite='strict',max_age=86400)
    return {'csrf':csrf}

@app.get('/api/session')
async def session(entry=Depends(owner)):
    return {'csrf':entry['csrf'],'provider':os.getenv('LLM_PROVIDER','agent_router'),'model':os.getenv('LLM_MODEL','gpt-6.1-sol'),'configured':bool(os.getenv('LLM_API_KEY'))}
@app.post('/api/logout')
async def logout(request:Request,response:Response,entry=Depends(owner)):
    sessions.pop(hashlib.sha256(request.cookies.get('browser_lite_session','').encode()).hexdigest(),None)
    response.delete_cookie('browser_lite_session');return {'ok':True}

class TaskBody(BaseModel):
    url:str=Field(default='',max_length=2048)
    instruction:str=Field(min_length=1,max_length=12000)
    allow_actions:bool=False
class URLBody(BaseModel):url:str=Field(max_length=2048)
class InputBody(BaseModel):
    kind:str
    x:float=0
    y:float=0
    delta:float=0
    text:str=Field(default='',max_length=4000)
    key:str=''

@app.get('/healthz')
def health():return {'ok':True}
@app.get('/api/state',dependencies=[Depends(owner)])
def state():
    return {'task':engine.task,'browser_ready':engine.browser is not None,'busy':bool(engine.job and not engine.job.done()),'files':files(),'viewport':engine.viewport,'proxy':engine.proxy_info()}
@app.get('/api/history',dependencies=[Depends(owner)])
def history():return store.history()
@app.post('/api/tasks',dependencies=[Depends(owner)])
async def start(body:TaskBody):
    if not body.instruction.strip():raise HTTPException(422,'اكتب المهمة')
    try:return await engine.start(body.url,body.instruction,body.allow_actions)
    except ValueError as e:raise HTTPException(409 if engine.job and not engine.job.done() else 422,str(e))
class MessageBody(BaseModel):
    text:str=Field(min_length=1,max_length=12000)
    edit_id:str|None=None
class ProxyBody(BaseModel):
    enabled:bool=False
    url:str=Field(default='',max_length=2048)
    username:str=Field(default='',max_length=255)
    password:str=Field(default='',max_length=512)
    keep_password:bool=True
@app.post('/api/messages',dependencies=[Depends(owner)])
async def message(body:MessageBody):
    try:return await engine.message(body.text,body.edit_id)
    except ValueError as e:raise HTTPException(422,str(e))
@app.get('/api/proxy',dependencies=[Depends(owner)])
async def proxy_info():return engine.proxy_info()
@app.put('/api/proxy',dependencies=[Depends(owner)])
async def proxy_config(body:ProxyBody):
    try:return await engine.configure_proxy(**body.model_dump())
    except ValueError as e:raise HTTPException(409 if engine.job and not engine.job.done() else 422,str(e))
@app.post('/api/proxy/test',dependencies=[Depends(owner)])
async def proxy_test():
    import ipaddress
    async with engine.lock:
        if engine.job and not engine.job.done():raise HTTPException(409,'أوقف المهمة قبل فحص البروكسي')
        if not engine.proxy_config.get('enabled'):raise HTTPException(422,'فعّل بروكسي أولًا')
        try:
            await asyncio.wait_for(engine.navigate('https://api.ipify.org?format=json'),35)
            session=await engine.browser.get_or_create_cdp_session()
            result=await session.cdp_client.send.Runtime.evaluate(params={'expression':'document.body.innerText','returnByValue':True},session_id=session.session_id)
            text=result.get('result',{}).get('value','')
            ip=str(ipaddress.ip_address(json.loads(text)['ip']))
            engine.proxy_check={'ok':True,'ip':ip,'time':time.time()}
            engine.event('proxy','نجح فحص عنوان الخروج عبر البروكسي')
            return engine.proxy_check
        except Exception:
            engine.proxy_check={'ok':False,'time':time.time()}
            raise HTTPException(502,'فشل فحص البروكسي. الاتصال المباشر لن يُستخدم كبديل.')

@app.post('/api/control/{action}',dependencies=[Depends(owner)])
async def control(action:str):
    try:
        if action=='pause':await engine.pause()
        elif action=='cancel':await engine.pause(cancel=True)
        elif action=='resume':await engine.resume()
        elif action=='approve':await engine.approve()
        else:raise HTTPException(404)
        return {'ok':True}
    except ValueError as e:raise HTTPException(409,str(e))
@app.post('/api/browser/open',dependencies=[Depends(owner)])
async def open_page(body:URLBody):
    async with engine.lock:
        if engine.job and not engine.job.done():raise HTTPException(409,'استلم التحكم أولًا')
        try:
            await engine.navigate(body.url)
            return {'ok':True}
        except ValueError as e:raise HTTPException(422,str(e))
        except Exception as e:raise HTTPException(502,f'تعذر فتح المتصفح ({type(e).__name__})')
@app.post('/api/browser/input',dependencies=[Depends(owner)])
async def browser_input(body:InputBody):
    try:
        await engine.input(body.model_dump());return {'ok':True}
    except ValueError as e:raise HTTPException(409,str(e))
@app.post('/api/browser/clear',dependencies=[Depends(owner)])
async def clear():
    if engine.job and not engine.job.done():raise HTTPException(409,'أوقف المهمة أولًا')
    await engine.close_browser()
    shutil.rmtree(store.root/'profile',ignore_errors=True)
    return {'ok':True}

@app.websocket('/api/browser/live')
async def live(ws:WebSocket):
    try:
        if not same_origin(ws):raise ValueError()
        entry=authenticate(ws)
    except Exception:
        await ws.close(code=1008);return
    await ws.accept()
    try:
        while True:
            try:authenticate(ws)
            except HTTPException:break
            if engine.browser:
                try:
                    data=await asyncio.wait_for(engine.snapshot(),8)
                    url=await engine.browser.get_current_page_url()
                    await asyncio.wait_for(ws.send_json({'url':url}),5)
                    if engine.task and url.startswith(('https://','http://')) and engine.task.get('last_url')!=url:
                        engine.update(last_url=url)
                    await asyncio.wait_for(ws.send_bytes(data),5)
                except asyncio.TimeoutError:break
                except Exception:
                    await ws.send_json({'status':'waiting'})
            else:await ws.send_json({'status':'closed'})
            await asyncio.sleep(0.7)
    except (WebSocketDisconnect,RuntimeError):pass
    finally:
        try:await ws.close()
        except Exception:pass

@app.get('/api/events',dependencies=[Depends(owner)])
async def events(request:Request):
    async def generate():
        old=None
        while not await request.is_disconnected():
            try:authenticate(request)
            except HTTPException:break
            data=json.dumps(state(),ensure_ascii=False)
            if data!=old:
                yield f'data: {data}\n\n';old=data
            else:yield ': keepalive\n\n'
            await asyncio.sleep(1)
    return StreamingResponse(generate(),media_type='text/event-stream')

def files():
    d=store.root/'downloads'
    if not d.exists():return []
    return [{'name':p.name,'size':p.stat().st_size} for p in d.iterdir() if p.is_file() and not p.is_symlink() and p.stat().st_size<=10*1024**2][:30]
@app.get('/api/files/{name}',dependencies=[Depends(owner)])
def download(name:str):
    directory=(store.root/'downloads').resolve()
    path=(directory/name).resolve()
    if path.parent!=directory or not path.is_file() or path.stat().st_size>10*1024**2:raise HTTPException(404)
    return FileResponse(path,filename=path.name,media_type='application/octet-stream')

@app.post('/api/model/test',dependencies=[Depends(owner)])
async def model_test():
    from browser_use.llm.messages import UserMessage
    from pydantic import BaseModel
    class Probe(BaseModel):ok:bool
    try:
        result=await asyncio.wait_for(engine.llm().ainvoke([UserMessage(content='Return ok=true. This is a connection and structured-output test.')],output_format=Probe),30)
        return {'ok':result.completion.ok}
    except Exception as e:
        code=getattr(e,'status_code',None)
        raise HTTPException(502,f'فشل اختبار الموديل: {type(e).__name__}'+(f' ({code})' if code else ''))

@app.get('/sw.js')
def worker():return FileResponse(ROOT/'static/sw.js',media_type='application/javascript')

@app.get('/')
def index():return FileResponse(ROOT/'static/index.html')
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
