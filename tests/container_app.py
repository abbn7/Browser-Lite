"""Test-only deterministic provider. NEVER imported by the production entrypoint."""
import sys
sys.path.insert(0,'/app')
from container_smoke import Model
import app,uvicorn
app.engine.llm=lambda:Model()
uvicorn.run(app.app,host='0.0.0.0',port=8000,access_log=False)
