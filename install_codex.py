"""Install the official, pinned Codex binary; verify npm SHA-512 integrity."""
import base64,hashlib,io,json,os,platform,ssl,tarfile,urllib.request
version='0.163.0'
arch={'x86_64':'x64','aarch64':'arm64'}[platform.machine()]
context=ssl.create_default_context(cafile=os.getenv('SSL_CERT_FILE') or None)
def fetch(url):
    with urllib.request.urlopen(url,context=context,timeout=120) as response:return response.read()
meta=json.loads(fetch(f'https://registry.npmjs.org/@openai/codex/{version}-linux-{arch}'))
archive=fetch(meta['dist']['tarball'])
expected=meta['dist']['integrity']
if expected!='sha512-'+base64.b64encode(hashlib.sha512(archive).digest()).decode():raise RuntimeError('Codex package integrity mismatch')
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tar:
    binaries=[m for m in tar.getmembers() if m.isfile() and (m.name.endswith('/codex/codex') or m.name.endswith('/bin/codex'))]
    if len(binaries)!=1:raise RuntimeError('Unexpected Codex package layout')
    with open('/usr/local/bin/codex','wb') as output:output.write(tar.extractfile(binaries[0]).read())
os.chmod('/usr/local/bin/codex',0o755)
