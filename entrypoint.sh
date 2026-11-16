#!/bin/sh
set -eu
if [ ! -f /config/config.py ]; then cp /opt/mightymouse/config-example.py /config/config.py; echo 'Created /config/config.py; configure it first.'; fi
ln -sf /config/config.py /opt/mightymouse/config.py
mkdir -p /config/storage /staging /watch /blocked /data/mam-seed
rm -rf /opt/mightymouse/storage
ln -s /config/storage /opt/mightymouse/storage

# Environment DRY_RUN is authoritative.
python - <<'PYCFG'
import os,pathlib,re
p=pathlib.Path('/config/config.py');s=p.read_text();v=os.getenv('DRY_RUN','true').lower() in ('1','true','yes','on');line=f'DRY_RUN = {v}'
if re.search(r'^DRY_RUN\s*=.*$',s,re.M):s=re.sub(r'^DRY_RUN\s*=.*$',line,s,flags=re.M)
else:s+='\n'+line+'\n'
p.write_text(s)
PYCFG

exec python /opt/controller/supervisor.py
