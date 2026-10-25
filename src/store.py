"""Local DuckDB repository. Original inputs and rejected hands remain recoverable."""
from pathlib import Path
from hashlib import sha256
import json, os, tempfile, uuid
import duckdb
from .history import read_text, PARSER_VERSION
from .engine import replay
from .context import CONTEXT_TYPES, ANALYSIS_VERSION
from .profiles import PROFILES
from .migrations import backup_database, SCHEMA_VERSION


def default_path():
    base=Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local/share'))
    return base/'SpinPopulationLab'/'population.duckdb'


OBS_TYPES={
 'hand_id':'VARCHAR','seq':'INTEGER','session':'VARCHAR','actor':'VARCHAR','opponent':'VARCHAR','opponents':'VARCHAR[]',
 'stake':'VARCHAR','format':'VARCHAR','modality':'VARCHAR','street':'INTEGER','position':'VARCHAR','spot':'VARCHAR',
 'path':'VARCHAR','previous':'VARCHAR','bb_eff':'DOUBLE','bb_eff_min':'DOUBLE','facing_bb':'DOUBLE','facing_pct':'DOUBLE',
 'board':'VARCHAR','texture':'VARCHAR','pot':'DOUBLE','remaining':'DOUBLE','result':'VARCHAR','allin':'BOOLEAN',
 'check_raise_opportunity':'BOOLEAN','can_raise':'BOOLEAN','eligible':'VARCHAR[]','size_bb':'DOUBLE','size_pct':'DOUBLE','known_cards':'VARCHAR','card_source':'VARCHAR'}

OBS_TYPES.update(CONTEXT_TYPES)

class Store:
    def __init__(self,path=None,progress=None,cancelled=None):
        self.path=Path(path or default_path()); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.con=duckdb.connect(str(self.path))
        self.con.execute('SET threads=4')
        old_tables={r[0] for r in self.con.execute('SHOW TABLES').fetchall()}
        if old_tables and 'metadata' not in old_tables:
            self.con.close();raise ValueError('La base no pertenece a Spin Population Lab.')
        version=self.con.execute('SELECT version FROM metadata').fetchone()[0] if 'metadata' in old_tables else SCHEMA_VERSION
        if version not in (1,SCHEMA_VERSION):
            self.con.close();raise ValueError('Unsupported database version')
        self.migration_backup=backup_database(self.path,self.con,'schema-1-to-2') if version==1 else None
        self.con.execute('''CREATE TABLE IF NOT EXISTS metadata(version INTEGER);
        INSERT INTO metadata SELECT 2 WHERE NOT EXISTS (SELECT 1 FROM metadata);
        CREATE TABLE IF NOT EXISTS imports(digest VARCHAR PRIMARY KEY, source VARCHAR, archived VARCHAR, report JSON);
        CREATE TABLE IF NOT EXISTS hands(hand_id VARCHAR PRIMARY KEY, tournament VARCHAR, stake VARCHAR, format VARCHAR, played_at VARCHAR, raw VARCHAR, digest VARCHAR, parser VARCHAR, pot BIGINT, players JSON, events JSON);
        CREATE TABLE IF NOT EXISTS errors(id VARCHAR, source VARCHAR, hand_id VARCHAR, error VARCHAR, raw VARCHAR);
        CREATE TABLE IF NOT EXISTS summaries(tournament VARCHAR, digest VARCHAR PRIMARY KEY, raw VARCHAR);
        CREATE TABLE IF NOT EXISTS labels(player VARCHAR PRIMARY KEY, category VARCHAR, origin VARCHAR, confidence DOUBLE, reason VARCHAR);
        CREATE TABLE IF NOT EXISTS documents(kind VARCHAR, name VARCHAR, payload JSON, PRIMARY KEY(kind,name));''')
        self.con.execute('CREATE TABLE IF NOT EXISTS label_history(id VARCHAR, player VARCHAR, category VARCHAR, origin VARCHAR, confidence DOUBLE, reason VARCHAR, recorded_at TIMESTAMP DEFAULT current_timestamp)')
        self.con.execute('CREATE TABLE IF NOT EXISTS analysis_metadata(version INTEGER)')
        self.con.execute('CREATE TABLE IF NOT EXISTS observations('+','.join('"'+k+'" '+v for k,v in OBS_TYPES.items())+', PRIMARY KEY(hand_id,seq))')
        if version==1:
            try:
                self.con.execute('BEGIN')
                existing={r[1] for r in self.con.execute("PRAGMA table_info('observations')").fetchall()}
                for name,typ in OBS_TYPES.items():
                    if name not in existing:self.con.execute(f'ALTER TABLE observations ADD COLUMN "{name}" {typ}')
                self.rebuild_analysis(transaction=False,backup=False,progress=progress,cancelled=cancelled)
                self.con.execute('UPDATE metadata SET version=2')
                self.con.execute('COMMIT')
            except Exception:
                self.con.execute('ROLLBACK');self.con.close();raise
        if not self.con.execute('SELECT count(*) FROM analysis_metadata').fetchone()[0]:
            self.con.execute('INSERT INTO analysis_metadata VALUES (?)',[ANALYSIS_VERSION])
        elif self.con.execute('SELECT version FROM analysis_metadata').fetchone()[0] < ANALYSIS_VERSION:
            try:
                self.rebuild_analysis(progress=progress,cancelled=cancelled)
            except Exception:
                self.con.close();raise

    def rebuild_analysis(self,transaction=True,backup=True,progress=None,cancelled=None):
        # Original hands are immutable; regenerate derived observations transactionally.
        if backup:backup_database(self.path,self.con,'rebuild')
        if transaction:self.con.execute('BEGIN')
        try:
            self.con.execute('DELETE FROM observations')
            cursor=''; total=0
            while True:
                batch=self.con.execute('SELECT hand_id,raw FROM hands WHERE hand_id>? ORDER BY hand_id LIMIT 1000',[cursor]).fetchall()
                if not batch: break
                if cancelled and cancelled():raise InterruptedError('Rebuild cancelled; previous observations retained')
                rows=[]
                for ident,raw in batch:
                    hands,errors,_=read_text(raw.encode())
                    if errors or len(hands)!=1: raise ValueError('Stored hand no longer parses: '+ident)
                    rows.extend(replay(hands[0])[0])
                self.bulk('observations',rows,OBS_TYPES);total+=len(rows);cursor=batch[-1][0]
                if progress:progress(total)
            self.con.execute('UPDATE hands SET parser=?',[PARSER_VERSION])
            self.con.execute('DELETE FROM analysis_metadata')
            self.con.execute('INSERT INTO analysis_metadata VALUES (?)',[ANALYSIS_VERSION])
            if transaction:self.con.execute('COMMIT')
            return total
        except Exception:
            if transaction:self.con.execute('ROLLBACK')
            raise

    def close(self): self.con.close()

    def rows(self,sql,args=None):
        cur=self.con.execute(sql,args or []); names=[d[0] for d in cur.description]
        return [dict(zip(names,row)) for row in cur.fetchall()]

    def bulk(self,table,rows,types):
        if not rows: return
        with tempfile.NamedTemporaryFile(mode='w',suffix='.json',encoding='utf-8',delete=False) as f:
            for row in rows: f.write(json.dumps(row,ensure_ascii=False)+'\n')
            name=f.name
        try:
            self.con.execute(f'INSERT INTO {table} BY NAME SELECT * FROM read_json(?, columns={json.dumps(types)}, format=\'newline_delimited\')',[name])
        finally: Path(name).unlink()

    def import_file(self,path):
        path=Path(path); data=path.read_bytes(); digest=sha256(data).hexdigest()
        previous=self.con.execute('SELECT report FROM imports WHERE digest=?',[digest]).fetchone()
        if previous: return dict(added=0,duplicates=0,conflicts=0,rejected=0,observations=0,summaries=0,already_imported=True,previous_report=json.loads(previous[0]))
        archive=self.path.parent/'imports'; archive.mkdir(exist_ok=True)
        saved=archive/(digest+'.txt')
        if not saved.exists(): saved.write_bytes(data)
        hs=[]; errs=[]; summary=None
        try: hs,errs,summary=read_text(data)
        except (ValueError,UnicodeError) as e: errs=[dict(hand_id='',error=str(e),raw='')]
        report=dict(added=0,duplicates=0,conflicts=0,rejected=len(errs),observations=0,summaries=int(summary is not None),already_imported=False)
        handrows=[]; observations=[]
        existing=dict(self.con.execute('SELECT hand_id,digest FROM hands WHERE hand_id IN (SELECT unnest(?))',[[h.hand_id for h in hs]]).fetchall()) if hs else {}
        for h in hs:
            canonical='\n'.join(l.rstrip() for l in h.raw.strip().splitlines()); fingerprint=sha256(canonical.encode()).hexdigest()
            if h.hand_id in existing:
                if existing[h.hand_id]==fingerprint: report['duplicates']+=1
                else:
                    report['conflicts']+=1; errs.append(dict(hand_id=h.hand_id,error='Conflicting duplicate; original retained',raw=h.raw))
                continue
            try: oo,ee,balance=replay(h)
            except ValueError as e:
                report['rejected']+=1; errs.append(dict(hand_id=h.hand_id,error=str(e),raw=h.raw)); continue
            existing[h.hand_id]=fingerprint
            handrows.append(dict(hand_id=h.hand_id,tournament=h.tournament,stake=h.stake,format=h.format,played_at=h.played_at,raw=h.raw,digest=fingerprint,parser=PARSER_VERSION,pot=h.pot,players=json.dumps(h.players),events=json.dumps(ee)))
            observations.extend(oo)
        report['added']=len(handrows); report['observations']=len(observations)
        self.con.execute('BEGIN')
        try:
            self.bulk('hands',handrows,dict(hand_id='VARCHAR',tournament='VARCHAR',stake='VARCHAR',format='VARCHAR',played_at='VARCHAR',raw='VARCHAR',digest='VARCHAR',parser='VARCHAR',pot='BIGINT',players='JSON',events='JSON'))
            self.bulk('observations',observations,OBS_TYPES)
            self.bulk('errors',[dict(id=str(uuid.uuid4()),source=path.name,**e) for e in errs],dict(id='VARCHAR',source='VARCHAR',hand_id='VARCHAR',error='VARCHAR',raw='VARCHAR'))
            if summary: self.con.execute('INSERT INTO summaries VALUES (?,?,?)',[summary['tournament'],digest,summary['raw']])
            self.con.execute('INSERT INTO imports VALUES (?,?,?,?)',[digest,path.name,str(saved),json.dumps(report)])
            self.con.execute('COMMIT')
        except Exception:
            self.con.execute('ROLLBACK'); raise
        return report

    def label(self,player,category,origin='manual',confidence=None,reason='Asignación del usuario',profile=None,transaction=True):
        if category not in ('Reg','Fish','Sin clasificar'): raise ValueError('Invalid category')
        if profile is not None and profile not in PROFILES[category]:raise ValueError('Perfil incompatible con categoría')
        if transaction:self.con.execute('BEGIN')
        try:
            self.con.execute('INSERT INTO label_history(id,player,category,origin,confidence,reason) VALUES (?,?,?,?,?,?)',[str(uuid.uuid4()),player,category,origin,confidence,reason])
            self.con.execute('INSERT INTO labels VALUES (?,?,?,?,?) ON CONFLICT(player) DO UPDATE SET category=excluded.category, origin=excluded.origin, confidence=excluded.confidence, reason=excluded.reason',[player,category,origin,confidence,reason])
            self.save_document('player_profile',player,dict(profile=profile,category=category))
            if transaction:self.con.execute('COMMIT')
        except Exception:
            if transaction:self.con.execute('ROLLBACK')
            raise

    def save_document(self,kind,name,payload):
        if not name.strip(): raise ValueError('Nombre obligatorio')
        self.con.execute('INSERT INTO documents VALUES (?,?,?) ON CONFLICT(kind,name) DO UPDATE SET payload=excluded.payload',[kind,name,json.dumps(payload)])

    def documents(self,kind):
        return [dict(name=n,payload=json.loads(p)) for n,p in self.con.execute('SELECT name,payload FROM documents WHERE kind=? ORDER BY name',[kind]).fetchall()]

    def totals(self):
        return {t:self.con.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in ('hands','observations','summaries','errors')}
