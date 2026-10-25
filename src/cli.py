import argparse,json
from pathlib import Path
from collections import Counter
from .store import Store

def main():
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['import','status','rebuild']);p.add_argument('--db',type=Path);p.add_argument('paths',nargs='*',type=Path)
    a=p.parse_args();s=Store(a.db)
    try:
        report=Counter()
        if a.command=='rebuild':report['rebuilt_observations']=s.rebuild_analysis()
        for path in a.paths:
            files=sorted(path.rglob('*.txt')) if path.is_dir() else [path]
            for f in files:
                result=s.import_file(f)
                report.update({k:v for k,v in result.items() if isinstance(v,int)})
        print(json.dumps(dict(import_report=report,totals=s.totals()),indent=2))
    finally:s.close()
if __name__=='__main__':main()
