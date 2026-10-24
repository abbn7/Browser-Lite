import asyncio,base64,json,os,sys,tempfile
from pathlib import Path
import pytest
from pydantic import BaseModel
from providers import CodexModel
from browser_use.llm.messages import UserMessage

class Probe(BaseModel):ok:bool

def test_cli_transport_uses_schema_and_no_shell(monkeypatch,tmp_path):
    binary=tmp_path/'codex'
    binary.write_text('''#!/usr/bin/env python3
import json,sys,os,pathlib
args=sys.argv[1:]
assert '--ignore-user-config' in args and '--ephemeral' in args
assert 'shell_tool' in args and 'unified_exec' in args
assert os.environ['CODEX_GATEWAY_API_KEY']=='test-key'
assert 'APP_PASSWORD' not in os.environ
assert 'LLM_API_KEY' not in os.environ
assert 'test-key' not in ' '.join(args)
schema=json.load(open(args[args.index('--output-schema')+1]))
assert schema['additionalProperties'] is False
assert json.loads(sys.stdin.read().split('\\n',1)[1])[0]['content']=='Return ok=true'
pathlib.Path(args[args.index('-o')+1]).write_text('{"ok":true}')
''')
    binary.chmod(0o700)
    monkeypatch.setenv('CODEX_BINARY',str(binary))
    monkeypatch.setenv('APP_PASSWORD','private-password')
    monkeypatch.setenv('LLM_API_KEY','private-key')
    result=asyncio.run(CodexModel('model','test-key','https://example.com/v1').ainvoke([UserMessage(content='Return ok=true')],output_format=Probe))
    assert result.completion.ok

def test_cli_timeout_terminates_process(monkeypatch,tmp_path):
    binary=tmp_path/'codex'
    pidfile=tmp_path/'pid'
    binary.write_text(f'#!/usr/bin/env python3\nimport os,time,pathlib\npathlib.Path({str(pidfile)!r}).write_text(str(os.getpid()))\ntime.sleep(60)\n')
    binary.chmod(0o700)
    monkeypatch.setenv('CODEX_BINARY',str(binary));monkeypatch.setenv('MODEL_TIMEOUT_SECONDS','1')
    with pytest.raises(TimeoutError):
        asyncio.run(CodexModel('model','test-key','https://example.com/v1').ainvoke([UserMessage(content='test')],output_format=Probe))
    with pytest.raises(ProcessLookupError):os.kill(int(pidfile.read_text()),0)
