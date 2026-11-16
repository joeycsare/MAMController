#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path
import requests

BASE=os.getenv('MAM_BASE_URL','https://www.myanonamouse.net').rstrip('/')
CONFIG=Path(os.getenv('MAM_CONFIG','/config/config.py'))
STATE=Path(os.getenv('MAM_API_HEALTH_FILE','/config/mam-api-health.json'))
TIMEOUT=int(os.getenv('MAM_API_HEALTH_TIMEOUT','12'))


def read_mam_id():
    ns={}
    exec(compile(CONFIG.read_text(),str(CONFIG),'exec'),ns)
    return str(ns.get('MAM_ID','')).strip()

def fail(reason, detail=''):
    state={'healthy':False,'checked_at':int(time.time()),'reason':reason,'detail':detail[:500]}
    STATE.write_text(json.dumps(state,indent=2))
    print('MAM API unhealthy:',reason,detail,file=sys.stderr)
    return 1

def main():
    try: mam=read_mam_id()
    except Exception as e: return fail('config_error',str(e))
    if not mam: return fail('missing_mam_id')
    s=requests.Session(); h={'Cookie':f'mam_id={mam}','Accept':'application/json'}
    try:
        a=s.get(BASE+'/jsonLoad.php',headers=h,timeout=TIMEOUT)
        if a.status_code!=200: return fail('user_http',str(a.status_code))
        simple=a.json()
        b=s.get(BASE+'/jsonLoad.php?snatch_summary',headers=h,timeout=TIMEOUT)
        if b.status_code!=200: return fail('summary_http',str(b.status_code))
        advanced=b.json()
    except requests.RequestException as e: return fail('network_error',str(e))
    except ValueError as e: return fail('invalid_json',str(e))
    if not isinstance(simple,dict) or not isinstance(simple.get('username'),str): return fail('user_schema','missing username')
    required=('classname','seedbonus')
    missing=[k for k in required if k not in advanced]
    if not isinstance(advanced,dict) or missing: return fail('summary_schema','missing '+','.join(missing))
    STATE.write_text(json.dumps({'healthy':True,'checked_at':int(time.time()),'username':simple['username']},indent=2))
    print('MAM API healthy')
    return 0
if __name__=='__main__': raise SystemExit(main())
