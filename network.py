"""Fail-closed browser egress. HTTP(S) CONNECT and SOCKS4a/5 upstreams."""
import asyncio, base64, ipaddress, os, ssl, struct
from urllib.parse import urlsplit,unquote

def check_host(host,port):
    if port not in (80,443):raise ValueError('Only public HTTP/HTTPS ports are supported')
    host=host.rstrip('.').lower()
    if host=='localhost' or host.endswith(('.localhost','.local','.internal')):raise ValueError('Private destinations are blocked')
    try:
        if not ipaddress.ip_address(host).is_global:raise ValueError('Private destinations are blocked')
    except ValueError as e:
        if 'Private' in str(e):raise
    return host

async def public_address(host,port):
    host=check_host(host,port)
    records=await asyncio.get_running_loop().getaddrinfo(host,port,type=1)
    addresses=list(dict.fromkeys(r[4][0] for r in records))
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):raise ValueError('Private destinations are blocked')
    return addresses[0]

async def validate_url(url,remote_dns=False):
    p=urlsplit(url)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password:raise ValueError('Use a public HTTP or HTTPS URL without credentials')
    port=p.port or (443 if p.scheme=='https' else 80)
    check_host(p.hostname,port)
    if not remote_dns:await public_address(p.hostname,port)
    return url

def parse_proxy(url,username='',password=''):
    p=urlsplit(url.strip())
    if p.scheme not in ('http','https','socks5','socks5h','socks4','socks4a') or not p.hostname or p.path not in ('','/') or p.query or p.fragment:
        raise ValueError('Use http://, https://, socks5:// or socks4a://host:port')
    port=p.port or {'http':80,'https':443,'socks5':1080,'socks5h':1080,'socks4':1080,'socks4a':1080}[p.scheme]
    if not 1<=port<=65535:raise ValueError('Invalid proxy port')
    user=username or unquote(p.username or '')
    secret=password or unquote(p.password or '')
    if p.scheme in ('socks4','socks4a') and secret:raise ValueError('SOCKS4a supports a user ID, not password authentication; use SOCKS5')
    return {'scheme':p.scheme,'host':p.hostname,'port':port,'username':user,'password':secret}

def proxy_url(config):
    host=config['host'];host=f'[{host}]' if ':' in host else host
    return f"{config['scheme']}://{host}:{config['port']}"

def auth_header(config):
    if not config.get('username') and not config.get('password'):return b''
    token=base64.b64encode((config.get('username','')+':'+config.get('password','')).encode())
    return b'Proxy-Authorization: Basic '+token+b'\r\n'

async def http_tunnel(reader,writer,config,host,port):
    authority=f'[{host}]:{port}' if ':' in host else f'{host}:{port}'
    writer.write(f'CONNECT {authority} HTTP/1.1\r\nHost: {authority}\r\n'.encode()+auth_header(config)+b'\r\n')
    await writer.drain()
    response=await reader.readuntil(b'\r\n\r\n')
    if b' 200 ' not in response.split(b'\r\n')[0]:raise ConnectionError('Proxy rejected connection or authentication')

class PublicProxy:
    server=None
    def __init__(self):self.handlers=set();self.upstream=None
    @property
    def remote_dns(self):return self.upstream is not None
    async def start(self):
        self.server=await asyncio.start_server(self.handle,'127.0.0.1',0,limit=32768)
        return self.server.sockets[0].getsockname()[1]
    async def close(self):
        if self.server:self.server.close();await self.server.wait_closed()
        tasks=list(self.handlers)
        for task in tasks:task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
    async def open_endpoint(self,config):
        system=os.getenv('BROWSER_UPSTREAM_PROXY')
        try:local=ipaddress.ip_address(config['host']).is_loopback
        except ValueError:local=config['host']=='localhost'
        # Locally hosted proxies do not traverse the external environment gateway.
        if system and self.upstream and not local:
            outer=parse_proxy(system)
            if outer['scheme'] not in ('http','https'):raise ValueError('Environment proxy must be HTTP(S)')
            reader,writer=await asyncio.open_connection(outer['host'],outer['port'],ssl=ssl.create_default_context() if outer['scheme']=='https' else None)
            await http_tunnel(reader,writer,outer,config['host'],config['port'])
        else:
            reader,writer=await asyncio.open_connection(config['host'],config['port'])
        try:
            if config['scheme']=='https':await writer.start_tls(ssl.create_default_context(),server_hostname=config['host'])
            return reader,writer
        except BaseException:
            writer.close();raise
    async def tunnel(self,config,host,port):
        reader,writer=await self.open_endpoint(config)
        try:
            scheme=config['scheme']
            if scheme in ('http','https'):await http_tunnel(reader,writer,config,host,port)
            elif scheme in ('socks5','socks5h'):
                user=config.get('username','').encode();password=config.get('password','').encode()
                methods=b'\x00\x02' if user or password else b'\x00'
                writer.write(b'\x05'+bytes([len(methods)])+methods);await writer.drain()
                reply=await reader.readexactly(2)
                if reply[0]!=5 or reply[1] not in (0,2):raise ConnectionError('SOCKS5 auth method rejected')
                if reply[1]==2:
                    if len(user)>255 or len(password)>255:raise ValueError('SOCKS5 credentials too long')
                    writer.write(b'\x01'+bytes([len(user)])+user+bytes([len(password)])+password);await writer.drain()
                    if await reader.readexactly(2)!=b'\x01\x00':raise ConnectionError('SOCKS5 authentication rejected')
                domain=host.encode('idna')
                if len(domain)>255:raise ValueError('Hostname too long')
                writer.write(b'\x05\x01\x00\x03'+bytes([len(domain)])+domain+struct.pack('!H',port));await writer.drain()
                response=await reader.readexactly(4)
                if response[0]!=5 or response[1]!=0:raise ConnectionError('SOCKS5 connection rejected')
                count={1:4,4:16}.get(response[3])
                if response[3]==3:count=(await reader.readexactly(1))[0]
                if count is None:raise ConnectionError('Invalid SOCKS5 response')
                await reader.readexactly(count+2)
            else:
                user=config.get('username','').encode()
                if b'\x00' in user or len(user)>255:raise ValueError('Invalid SOCKS4 user')
                writer.write(b'\x04\x01'+struct.pack('!H',port)+b'\x00\x00\x00\x01'+user+b'\x00'+host.encode('idna')+b'\x00');await writer.drain()
                reply=await reader.readexactly(8)
                if reply[1]!=90:raise ConnectionError('SOCKS4 connection rejected')
            return reader,writer
        except BaseException:
            writer.close();raise
    async def handle(self,reader,writer):
        task=asyncio.current_task();self.handlers.add(task);remote=None
        try:
            header=await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'),15)
            method,target,version=header.split(b'\r\n',1)[0].decode().split(' ',2)
            parsed=urlsplit('https://'+target if method=='CONNECT' else target)
            host,port=parsed.hostname,parsed.port or (443 if method=='CONNECT' else 80)
            if not host or parsed.username or parsed.password:raise ValueError('Invalid target')
            check_host(host,port)
            config=self.upstream
            if config:
                # Target DNS stays with the upstream. There is no direct retry path.
                rr,remote=await asyncio.wait_for(self.tunnel(config,host,port),20)
            else:
                address=await public_address(host,port)
                system=os.getenv('BROWSER_UPSTREAM_PROXY')
                if system:rr,remote=await asyncio.wait_for(self.tunnel(parse_proxy(system),host,port),20)
                else:rr,remote=await asyncio.wait_for(asyncio.open_connection(address,port),15)
            if method=='CONNECT':writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            else:
                path=parsed.path or '/'
                if parsed.query:path+='?'+parsed.query
                lines=[x for x in header.split(b'\r\n')[1:] if not x.lower().startswith((b'proxy-',b'connection:'))]
                remote.write(f'{method} {path} {version}\r\n'.encode()+b'\r\n'.join(lines));await remote.drain()
            await writer.drain()
            async def pipe(src,dst):
                while data:=await src.read(65536):dst.write(data);await dst.drain()
            tasks=[asyncio.create_task(pipe(reader,remote)),asyncio.create_task(pipe(rr,writer))]
            try:await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
            finally:
                for item in tasks:item.cancel()
                await asyncio.gather(*tasks,return_exceptions=True)
        except (Exception,asyncio.CancelledError):
            try:writer.write(b'HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n');await writer.drain()
            except Exception:pass
        finally:
            if remote:remote.close()
            writer.close();self.handlers.discard(task)
