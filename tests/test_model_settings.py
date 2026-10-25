import asyncio,json
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from model_settings import ModelSettings
from store import Store

def test_encrypted_profiles_precedence_and_restart(tmp_path,monkeypatch):
 monkeypatch.setenv('LLM_API_KEY','environment-key');monkeypatch.setenv('LLM_PROVIDER','agent_router')
 settings=ModelSettings(Store(tmp_path))
 assert settings.active()['api_key']=='environment-key'
 profile=settings.resolve({'provider':'nvidia','model':'chosen-model','api_key':'private-nvidia-key'})
 settings.save(profile)
 assert b'private-nvidia-key' not in (tmp_path/'models.enc').read_bytes()
 assert 'private-nvidia-key' not in json.dumps(settings.public())
 restored=ModelSettings(Store(tmp_path));assert restored.active()['api_key']=='private-nvidia-key'
 assert restored.resolve({'provider':'nvidia','model':'other'})['api_key']=='private-nvidia-key'
 restored.delete('nvidia');assert restored.active()['api_key']=='environment-key'

@pytest.fixture
def client(tmp_path,monkeypatch):
 import app
 monkeypatch.setenv('APP_PASSWORD','unit-testing-password')
 monkeypatch.setattr(app.engine,'models',ModelSettings(Store(tmp_path)))
 async def valid(url):return url
 monkeypatch.setattr('network.validate_url',valid)
 with TestClient(app.app) as c:
  login=c.post('/api/login',json={'password':'unit-testing-password'},headers={'Origin':'http://testserver'})
  c.headers.update({'Origin':'http://testserver','X-CSRF-Token':login.json()['csrf']})
  yield c,app.engine

def test_api_profiles_masking_and_busy_guard(client,monkeypatch):
 c,e=client
 data={'provider':'openrouter','model':'test-model','api_key':'private-test-value','vision':False}
 assert c.put('/api/model/settings',json=data).status_code==200
 assert 'private-test-value' not in c.get('/api/model/settings').text
 assert c.get('/api/session').json()['model']=='test-model'
 monkeypatch.setattr(e,'job',SimpleNamespace(done=lambda:False))
 assert c.put('/api/model/settings',json=data).status_code==409
 assert c.delete('/api/model/settings/openrouter').status_code==409
 monkeypatch.setattr(e,'job',None)
 assert c.delete('/api/model/settings/openrouter').status_code==200

def test_draft_probe_uses_structured_output_and_does_not_save(client,monkeypatch):
 c,e=client
 class Model:
  async def ainvoke(self,messages,output_format):
   assert isinstance(messages[0].content,list)
   import base64,io
   from PIL import Image
   part=messages[0].content[1]
   Image.open(io.BytesIO(base64.b64decode(part.image_url.url.split(',')[1]))).verify()
   return SimpleNamespace(completion=output_format(ok=True))
 monkeypatch.setattr(e,'llm',lambda config:Model())
 result=c.post('/api/model/test',json={'provider':'nvidia','model':'vision-model','api_key':'probe-only','vision':True})
 assert result.status_code==200,result.text
 assert result.json()['vision_tested']
 assert 'nvidia' not in e.models.data()['profiles']

def test_validation_does_not_echo_credentials(client):
 c,_=client
 secret='sensitive-fixture-'+'x'*2050
 response=c.put('/api/model/settings',json={'provider':'nvidia','model':'m','api_key':secret})
 assert response.status_code==422
 assert 'sensitive-fixture' not in response.text
