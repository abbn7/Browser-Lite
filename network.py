"""HTTP CONNECT proxy: resolve and pin public addresses before browser egress."""
import asyncio, ipaddress, os
from urllib.parse import urlsplit

async def public_address(host: str, port: int):
    if port not in (80, 443):
        raise ValueError('Only public HTTP/HTTPS ports are supported')
    host = host.rstrip('.').lower()
    if host == 'localhost' or host.endswith(('.localhost', '.local', '.internal')):
        raise ValueError('Private destinations are blocked')
    records = await asyncio.get_running_loop().getaddrinfo(host, port, type=1)
    addresses = list(dict.fromkeys(r[4][0] for r in records))
    if not addresses or any(not ipaddress.ip_address(a).is_global for a in addresses):
        raise ValueError('Private destinations are blocked')
    return addresses[0]

async def validate_url(url: str):
    p = urlsplit(url)
    if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
        raise ValueError('Use a public HTTP or HTTPS URL without credentials')
    await public_address(p.hostname, p.port or (443 if p.scheme == 'https' else 80))
    return url

class PublicProxy:
    server = None
    def __init__(self):
        self.handlers=set()
    async def start(self):
        self.server = await asyncio.start_server(self.handle, '127.0.0.1', 0, limit=32768)
        return self.server.sockets[0].getsockname()[1]
    async def close(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        tasks=list(self.handlers)
        for task in tasks:task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
    async def handle(self, reader, writer):
        handler_task=asyncio.current_task()
        self.handlers.add(handler_task)
        remote = None
        try:
            header = await asyncio.wait_for(reader.readuntil(b'\r\n\r\n'), 15)
            method, target, version = header.split(b'\r\n', 1)[0].decode().split(' ', 2)
            parsed = urlsplit('https://' + target if method == 'CONNECT' else target)
            host, port = parsed.hostname, parsed.port or (443 if method == 'CONNECT' else 80)
            if not host or parsed.username or parsed.password:
                raise ValueError('Invalid target')
            address = await public_address(host, port)
            upstream = os.getenv('BROWSER_UPSTREAM_PROXY')
            if upstream:
                p = urlsplit(upstream)
                rr, remote = await asyncio.open_connection(p.hostname, p.port or 8080)
                # Preserve the environment's network proxy. Never bypass it.
                remote.write(header)
                await remote.drain()
                if method == 'CONNECT':
                    response = await rr.readuntil(b'\r\n\r\n')
                    writer.write(response)
                    if b' 200 ' not in response.split(b'\r\n')[0]:
                        return
            else:
                rr, remote = await asyncio.wait_for(asyncio.open_connection(address, port), 15)
                if method == 'CONNECT':
                    writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                else:
                    path = parsed.path or '/'
                    if parsed.query:
                        path += '?' + parsed.query
                    lines = header.split(b'\r\n')[1:]
                    lines = [x for x in lines if not x.lower().startswith((b'proxy-', b'connection:'))]
                    remote.write(f'{method} {path} {version}\r\n'.encode() + b'\r\n'.join(lines))
            await writer.drain()
            async def pipe(src, dst):
                while data := await src.read(65536):
                    dst.write(data)
                    await dst.drain()
            tasks = [asyncio.create_task(pipe(reader, remote)), asyncio.create_task(pipe(rr, writer))]
            try:
                await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
        except (Exception, asyncio.CancelledError):
            try:
                writer.write(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n')
                await writer.drain()
            except Exception:
                pass
        finally:
            if remote:
                remote.close()
            writer.close()
            self.handlers.discard(handler_task)
