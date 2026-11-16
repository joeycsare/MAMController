import hashlib,logging,os,shutil,time
from pathlib import Path
import bencodepy,qbittorrentapi
logging.basicConfig(level='INFO',format='%(asctime)s [storage] %(message)s')
S=Path('/staging');W=Path('/watch');B=Path('/blocked');CAP=int(float(os.getenv('STORAGE_LIMIT_GIB','300'))*1024**3);INT=max(2,int(os.getenv('STORAGE_GUARD_INTERVAL','5')));TO=max(15,int(os.getenv('STORAGE_GUARD_CONFIRM_TIMEOUT','90')));CATS={x.strip() for x in os.getenv('MAM_CATEGORIES','MAM_UNSAT,MAM_SAT').split(',')};DRY_RUN=os.getenv('DRY_RUN','true').lower() in ('1','true','yes','on')
for d in(S,W,B):d.mkdir(parents=True,exist_ok=True)
def conn():
 c=qbittorrentapi.Client(host=os.getenv('QBIT_HOST','gluetun'),port=int(os.getenv('QBIT_PORT','8080')),username=os.environ['QBIT_USERNAME'],password=os.environ['QBIT_PASSWORD']);c.auth_log_in();return c
def meta(p):
 m=bencodepy.decode(p.read_bytes());i=m[b'info'];h=hashlib.sha1(bencodepy.encode(i)).hexdigest();z=int(i[b'length']) if b'length' in i else sum(int(f[b'length']) for f in i.get(b'files',[]));return h,z
def state(c):
 ts=c.torrents_info();hs={str(t.hash).lower() for t in ts};used=sum(int(getattr(t,'total_size',0) or getattr(t,'size',0) or 0) for t in ts if str(getattr(t,'category','')) in CATS);return used,hs
def dest(d,n):
 p=d/n;k=1
 while p.exists():p=d/f'{Path(n).stem}-{k}{Path(n).suffix}';k+=1
 return p
def confirm(c,h):
 end=time.monotonic()+TO
 while time.monotonic()<end:
  if h in {str(t.hash).lower() for t in c.torrents_info()}:return True
  time.sleep(3)
 return False
c=None;logging.info('Hard cap %.2f GiB',CAP/1024**3)
while True:
 try:
  if c is None:c=conn()
  fs=sorted(S.rglob('*.torrent'),key=lambda p:p.stat().st_mtime)
  if not fs:time.sleep(INT);continue
  p=fs[0];h,z=meta(p);used,hs=state(c)
  if h in hs:shutil.move(p,dest(B,p.name+'.duplicate'));continue
  if z<=0:shutil.move(p,dest(B,p.name+'.invalid'));continue
  if used+z>CAP:logging.warning('BLOCK %s: %.2f + %.2f > %.2f GiB',p.name,used/1024**3,z/1024**3,CAP/1024**3);time.sleep(30);continue
  if DRY_RUN: logging.info('DRY RUN: would ADMIT %s projected %.2f/%.2f GiB',p.name,(used+z)/1024**3,CAP/1024**3);time.sleep(INT);continue
  q=dest(W,p.name);shutil.move(p,q);logging.info('ADMIT %s projected %.2f/%.2f GiB',p.name,(used+z)/1024**3,CAP/1024**3)
  if not confirm(c,h):
   if q.exists():shutil.move(q,dest(S,q.name))
   logging.error('No qBit confirmation; rolled back');time.sleep(30)
 except Exception as e:logging.error(e);c=None;time.sleep(max(INT,10))
