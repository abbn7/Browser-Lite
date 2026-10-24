import json, sqlite3, time
from pathlib import Path
class Store:
    def __init__(self, directory):
        self.root=Path(directory)
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.db=sqlite3.connect(self.root/'tasks.sqlite3')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, updated REAL, data TEXT)')
        self.db.commit()
    def save(self, task):
        self.db.execute('INSERT OR REPLACE INTO tasks VALUES(?,?,?)',(task['id'],time.time(),json.dumps(task,ensure_ascii=False)))
        self.db.commit()
    def latest(self):
        row=self.db.execute('SELECT data FROM tasks ORDER BY updated DESC LIMIT 1').fetchone()
        return json.loads(row[0]) if row else None
    def history(self):
        return [json.loads(row[0]) for row in self.db.execute('SELECT data FROM tasks ORDER BY updated DESC LIMIT 20')]
