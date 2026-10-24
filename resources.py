from pathlib import Path

def container_memory():
    try:
        current=int(Path('/sys/fs/cgroup/memory.current').read_text())
        limit=Path('/sys/fs/cgroup/memory.max').read_text().strip()
        stats=dict(line.split() for line in Path('/sys/fs/cgroup/memory.stat').read_text().splitlines())
        working=max(0,current-int(stats.get('inactive_file',0)))
        return working,int(limit) if limit!='max' else None
    except (OSError,ValueError):
        return None,None
