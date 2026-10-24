import asyncio,base64,json,tempfile
from urllib.parse import urlsplit
from network import PublicProxy,parse_proxy,validate_url
from store import Store
from engine import Engine

def test_proxy_credentials_encrypted_and_masked():
    async def run():
        with tempfile.TemporaryDirectory() as d:
            e=Engine(Store(d))
            info=await e.configure_proxy(True,'socks5://proxy.example:1080','owner','super-secret')
            assert info['has_password'] and 'super-secret' not in json.dumps(info)
            assert b'super-secret' not in (e.store.root/'proxy.enc').read_bytes()
            restored=Engine(Store(d));assert restored.proxy.upstream['password']=='super-secret'
            await e.configure_proxy(True,'socks5://proxy.example:1080','owner','',True)
            assert e.proxy.upstream['password']=='super-secret'
            await e.configure_proxy(False)
            assert not e.proxy.remote_dns
            await e.close();await restored.close()
    asyncio.run(run())

def test_proxy_protocols_and_remote_dns():
    async def run(scheme):
        seen=[]
        async def upstream(reader,writer):
            try:
                if scheme=='http':
                    header=await reader.readuntil(b'\r\n\r\n')
                    assert b'CONNECT remote-only.invalid:443' in header
                    assert b'Proxy-Authorization: Basic '+base64.b64encode(b'owner:secret') in header
                    writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n');await writer.drain()
                elif scheme=='socks5':
                    greeting=await reader.readexactly(2);methods=await reader.readexactly(greeting[1]);assert 2 in methods
                    writer.write(b'\x05\x02');await writer.drain()
                    auth=await reader.readexactly(2);user=await reader.readexactly(auth[1]);n=(await reader.readexactly(1))[0];password=await reader.readexactly(n)
                    assert user==b'owner' and password==b'secret'
                    writer.write(b'\x01\x00');await writer.drain()
                    head=await reader.readexactly(5);assert head[:4]==b'\x05\x01\x00\x03'
                    domain=await reader.readexactly(head[4]);port=await reader.readexactly(2)
                    assert domain==b'remote-only.invalid' and port==b'\x01\xbb'
                    writer.write(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00');await writer.drain()
                else:
                    head=await reader.readexactly(8);assert head==b'\x04\x01\x01\xbb\x00\x00\x00\x01'
                    user=await reader.readuntil(b'\x00');domain=await reader.readuntil(b'\x00')
                    assert user==b'owner\x00' and domain==b'remote-only.invalid\x00'
                    writer.write(b'\x00\x5a\x00\x00\x00\x00\x00\x00');await writer.drain()
                data=await reader.readexactly(4);assert data==b'PING';seen.append(True)
                writer.write(b'PONG');await writer.drain()
            finally:writer.close()
        server=await asyncio.start_server(upstream,'127.0.0.1',0)
        proxy=PublicProxy();proxy.upstream=parse_proxy(f'{scheme}://127.0.0.1:{server.sockets[0].getsockname()[1]}','owner','' if scheme=='socks4a' else 'secret')
        port=await proxy.start()
        try:
            reader,writer=await asyncio.open_connection('127.0.0.1',port)
            writer.write(b'CONNECT remote-only.invalid:443 HTTP/1.1\r\nHost: remote-only.invalid:443\r\n\r\n');await writer.drain()
            assert b' 200 ' in await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'),3)
            writer.write(b'PING');await writer.drain()
            assert await reader.readexactly(4)==b'PONG' and seen
            writer.close()
        finally:await proxy.close();server.close();await server.wait_closed()
    for scheme in ['http','socks5','socks4a']:asyncio.run(run(scheme))

def test_failed_proxy_never_connects_directly(monkeypatch):
    async def run():
        connector=asyncio.open_connection;calls=[]
        async def connect(host,port,*args,**kwargs):
            calls.append((host,port))
            if host=='broken.proxy':raise ConnectionError('offline')
            return await connector(host,port,*args,**kwargs)
        monkeypatch.setattr(asyncio,'open_connection',connect)
        proxy=PublicProxy();proxy.upstream=parse_proxy('http://broken.proxy:8000')
        port=await proxy.start()
        try:
            reader,writer=await connector('127.0.0.1',port)
            writer.write(b'CONNECT example.com:443 HTTP/1.1\r\n\r\n');await writer.drain()
            assert b' 502 ' in await reader.readuntil(b'\r\n\r\n')
            assert calls==[('broken.proxy',8000)]
            writer.close()
        finally:await proxy.close()
    asyncio.run(run())

def test_remote_dns_still_blocks_literal_private_targets():
    for url in ['https://127.0.0.1','https://[::1]','https://localhost','https://169.254.169.254']:
        try:asyncio.run(validate_url(url,remote_dns=True))
        except ValueError:pass
        else:raise AssertionError(url)

def test_https_upstream_uses_verified_tls(monkeypatch,tmp_path):
    import ssl,datetime,ipaddress
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes,serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'proxy-test')])
    now=datetime.datetime.now(datetime.timezone.utc)
    cert=(x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=1)).not_valid_after(now+datetime.timedelta(days=1)).add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False).sign(key,hashes.SHA256()))
    certfile=tmp_path/'cert.pem';keyfile=tmp_path/'key.pem'
    certfile.write_bytes(cert.public_bytes(serialization.Encoding.PEM));keyfile.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    original=ssl.create_default_context
    def trusted_context(*args,**kwargs):
        ctx=original(*args,**kwargs);ctx.load_verify_locations(str(certfile));assert ctx.check_hostname and ctx.verify_mode==ssl.CERT_REQUIRED;return ctx
    monkeypatch.setattr(ssl,'create_default_context',trusted_context)
    async def run():
        async def handler(reader,writer):
            try:
                header=await reader.readuntil(b'\r\n\r\n');assert b'CONNECT remote-only.invalid:443' in header
                writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n');await writer.drain()
                assert await reader.readexactly(4)==b'PING';writer.write(b'PONG');await writer.drain()
            finally:writer.close()
        server_context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);server_context.load_cert_chain(str(certfile),str(keyfile))
        server=await asyncio.start_server(handler,'127.0.0.1',0,ssl=server_context)
        proxy=PublicProxy();proxy.upstream=parse_proxy(f'https://127.0.0.1:{server.sockets[0].getsockname()[1]}');port=await proxy.start()
        try:
            reader,writer=await asyncio.open_connection('127.0.0.1',port)
            writer.write(b'CONNECT remote-only.invalid:443 HTTP/1.1\r\n\r\n');await writer.drain()
            assert b' 200 ' in await reader.readuntil(b'\r\n\r\n')
            writer.write(b'PING');await writer.drain();assert await reader.readexactly(4)==b'PONG';writer.close()
        finally:await proxy.close();server.close();await server.wait_closed()
    asyncio.run(run())
