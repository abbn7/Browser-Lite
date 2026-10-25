import json, sqlite3, time, threading
from pathlib import Path
class Store:
    def __init__(self, directory):
        self.root=Path(directory)
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.lock=threading.RLock()
        self.db=sqlite3.connect(self.root/'tasks.sqlite3',check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, updated REAL, data TEXT)')
        self.db.commit()
    def save(self, task):
        with self.lock:
            self.db.execute('INSERT OR REPLACE INTO tasks VALUES(?,?,?)',(task['id'],time.time(),json.dumps(task,ensure_ascii=False)))
            self.db.commit()
    def latest(self):
        with self.lock:row=self.db.execute('SELECT data FROM tasks ORDER BY updated DESC LIMIT 1').fetchone()
        return json.loads(row[0]) if row else None
    def history(self):
        with self.lock:return [json.loads(row[0]) for row in self.db.execute('SELECT data FROM tasks ORDER BY updated DESC LIMIT 20')]
    def secret(self,name):
        from cryptography.fernet import Fernet
        path=self.root/(name+'.enc')
        if not path.exists():return None
        return json.loads(self._cipher().decrypt(path.read_bytes()))
    def _cipher(self):
        from cryptography.fernet import Fernet
        import os
        path=self.root/'settings.key'
        key=os.getenv('SETTINGS_ENCRYPTION_KEY')
        if not key:
            if not path.exists():
                fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                with os.fdopen(fd,'wb') as f:f.write(Fernet.generate_key())
            key=path.read_bytes()
        return Fernet(key)
    def save_secret(self,name,data):
        import os,tempfile
        with self.lock:
            path=self.root/(name+'.enc')
            payload=self._cipher().encrypt(json.dumps(data).encode())
            fd,temporary=tempfile.mkstemp(prefix='.secret-',dir=self.root)
            try:
                with os.fdopen(fd,'wb') as f:
                    f.write(payload);f.flush();os.fsync(f.fileno())
                os.replace(temporary,path)
            finally:
                if os.path.exists(temporary):os.unlink(temporary)
