"""Checked database backups and schema/analysis migration infrastructure."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,shutil,uuid
import duckdb

SCHEMA_VERSION=2


def file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def backup_database(path, con, reason='manual'):
    """Call while this process has no writer task. CHECKPOINT includes the WAL."""
    path=Path(path);con.execute('CHECKPOINT')
    directory=path.parent/'backups';directory.mkdir(exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]
    target=directory/(path.stem+'-'+stamp+'.duckdb')
    shutil.copy2(path,target)
    if file_hash(path)!=file_hash(target):
        target.unlink();raise OSError('Backup verification failed')
    check=duckdb.connect(str(target),read_only=True)
    try:
        tables=[r[0] for r in check.execute('SHOW TABLES').fetchall()]
        counts={name:check.execute('SELECT count(*) FROM "'+name+'"').fetchone()[0] for name in tables}
    finally:check.close()
    manifest=dict(reason=reason,sha256=file_hash(target),tables=counts,original=str(path),
                  imports_directory=str(path.parent/'imports'),note='Original TXT files remain in imports/; retain that directory with backups.')
    target.with_suffix('.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    return target


def restore_copy(backup,destination):
    """Restore to a NEW destination, preserving both the current DB and archive."""
    backup=Path(backup);destination=Path(destination)
    if destination.exists():raise FileExistsError('La restauración requiere un archivo nuevo.')
    manifest=json.loads(backup.with_suffix('.json').read_text(encoding='utf-8'))
    if file_hash(backup)!=manifest['sha256']:raise ValueError('Backup checksum mismatch')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open('xb') as out,backup.open('rb') as inp:shutil.copyfileobj(inp,out)
    return destination
