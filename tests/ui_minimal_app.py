"""Test-only fixture routes. Excluded from Docker and never imported in production."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi import Depends
import app,uvicorn

@app.app.post('/__test/target',dependencies=[Depends(app.owner)])
async def target():
    session=await app.engine.browser.get_or_create_cdp_session()
    expression="""document.documentElement.style.cssText='margin:0;padding:0';document.body.style.cssText='margin:0;background:#e8e2d4;width:100vw;height:100vh;overflow:hidden';document.body.innerHTML='<div style="position:fixed;left:0;top:0;bottom:0;width:10%;background:#ce785e"></div><div style="position:fixed;right:0;top:0;bottom:0;width:10%;background:#302c27"></div><button id="target" style="position:absolute;left:590px;top:260px;width:100px;height:80px">target</button>';window.__hits=0;document.getElementById('target').onclick=()=>window.__hits++"""
    await session.cdp_client.send.Runtime.evaluate(params={'expression':expression},session_id=session.session_id)
    return {'ok':True}
@app.app.get('/__test/metrics',dependencies=[Depends(app.owner)])
async def metrics():
    session=await app.engine.browser.get_or_create_cdp_session()
    result=await session.cdp_client.send.Runtime.evaluate(params={'expression':'JSON.stringify({hits:window.__hits||0,innerWidth,innerHeight,screenWidth:screen.width,dpr:devicePixelRatio})','returnByValue':True},session_id=session.session_id)
    import json
    return json.loads(result['result']['value'])
if __name__=='__main__':uvicorn.run(app.app,host='127.0.0.1',port=8785,access_log=False)
