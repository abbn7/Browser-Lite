"""One active model profile; credentials stay encrypted on the server."""
import os
from urllib.parse import urlsplit
PRESETS={
 'agent_router':{'base_url':'https://agentrouter.org/v1','model':'gpt-6.1-sol'},
 'openrouter':{'base_url':'https://openrouter.ai/api/v1','model':'openrouter/free'},
 'google':{'base_url':'','model':'gemini-2.5-flash'},
 'nvidia':{'base_url':'https://integrate.api.nvidia.com/v1','model':''},
 'custom':{'base_url':'','model':''},
}
class ModelSettings:
 def __init__(self,store):self.store=store
 def data(self):return self.store.secret('models') or {'active':None,'profiles':{}}
 def environment(self):
  provider=os.getenv('LLM_PROVIDER','agent_router');preset=PRESETS.get(provider,{})
  return {'provider':provider,'base_url':os.getenv('LLM_BASE_URL') or preset.get('base_url',''),'model':os.getenv('LLM_MODEL') or preset.get('model',''),'api_key':os.getenv('LLM_API_KEY',''),'vision':os.getenv('USE_VISION','true').lower()=='true','transport':os.getenv('AGENT_ROUTER_TRANSPORT','codex')}
 def active(self):
  data=self.data();name=data.get('active')
  return dict(data['profiles'][name],provider=name) if name in data['profiles'] else self.environment()
 def public(self):
  data=self.data();active=self.active();profiles={}
  for name,preset in PRESETS.items():
   p=data['profiles'].get(name) or (active if name==active['provider'] else preset)
   profiles[name]={k:p.get(k,default) for k,default in [('base_url',''),('model',''),('vision',True)]}
   profiles[name]['has_key']=bool(p.get('api_key'))
  return {'active':active['provider'],'source':'saved' if data.get('active') else 'environment','profiles':profiles}
 def resolve(self,body):
  name=body['provider'];preset=PRESETS[name];old=self.data()['profiles'].get(name)
  if not old and self.environment()['provider']==name:old=self.environment()
  old=old or {}
  key=body.get('api_key') or old.get('api_key','')
  base=(body.get('base_url') or preset['base_url']).rstrip('/')
  parsed=urlsplit(base)
  if name!='google' and (parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment):raise ValueError('استخدم عنوان HTTPS صالحًا بدون بيانات دخول')
  model=body.get('model','').strip()
  if not model:raise ValueError('اكتب اسم الموديل')
  if not key:raise ValueError('أدخل مفتاح المزوّد')
  return {'provider':name,'api_key':key,'base_url':base,'model':model,'vision':body.get('vision',True),'transport':'codex' if name=='agent_router' else 'chat_completions'}
 def save(self,profile):
  data=self.data();name=profile['provider'];data['profiles'][name]={k:v for k,v in profile.items() if k!='provider'};data['active']=name;self.store.save_secret('models',data)
 def delete(self,name):
  data=self.data();data['profiles'].pop(name,None)
  if data.get('active')==name:data['active']=None
  self.store.save_secret('models',data)
