"""Real Chromium through an authenticated test proxy; uses environment egress."""
import asyncio,os,tempfile,base64,json
from urllib.parse import urlsplit
from engine import Engine
from store import Store
from network import http_tunnel,parse_proxy
async def main():
    records=[]
    async def proxy(reader,writer):
        remote=None
        try:
            header=await reader.readuntil(b'\r\n\r\n')
            if b'Proxy-Authorization: Basic '+base64.b64encode(b'test-user:test-password') not in header:
                writer.write(b'HTTP/1.1 407 Proxy Authentication Required\r\n\r\n');await writer.drain();return
            method,target,_=header.split(b'\r\n',1)[0].decode().split(' ',2)
            records.append(target)
            upstream=parse_proxy(os.environ['BROWSER_UPSTREAM_PROXY'])
            rr,remote=await asyncio.open_connection(upstream['host'],upstream['port'])
            remote.write(b'\r\n'.join(x for x in header.split(b'\r\n') if not x.lower().startswith(b'proxy-authorization:')));await remote.drain()
            async def pipe(src,dst):
                while data:=await src.read(65536):dst.write(data);await dst.drain()
            tasks=[asyncio.create_task(pipe(reader,remote)),asyncio.create_task(pipe(rr,writer))]
            try:await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
            finally:
                for task in tasks:task.cancel()
                await asyncio.gather(*tasks,return_exceptions=True)
        finally:
            if remote:remote.close()
            writer.close()
    server=await asyncio.start_server(proxy,'127.0.0.1',0)
    with tempfile.TemporaryDirectory() as d:
        e=Engine(Store(d))
        try:
            await e.configure_proxy(True,f'http://127.0.0.1:{server.sockets[0].getsockname()[1]}','test-user','test-password')
            await e.navigate('https://example.com')
            screenshot=await e.snapshot()
            from PIL import Image
            import io
            assert Image.open(io.BytesIO(screenshot)).size==(1280,800)
            assert any('example.com:443' in record for record in records)
            print(json.dumps({'authenticated_browser_proxy':True,'desktop_frame':[1280,800],'target_connections':len(records)}))
        finally:await e.close()
    server.close();await server.wait_closed()
asyncio.run(main())
