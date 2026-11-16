import ipaddress,logging,os,time,requests,qbittorrentapi
logging.basicConfig(level='INFO',format='%(asctime)s [bandwidth] %(message)s')
BANDWIDTH_DRY_RUN=os.getenv('BANDWIDTH_DRY_RUN','true').lower() in ('1','true','yes','on')
def ef(k,d):return float(os.getenv(k,d))
JF=os.getenv('JELLYFIN_URL','http://jellyfin:8096').rstrip('/'); KEY=os.environ['JELLYFIN_API_KEY']; POLL=max(5,int(os.getenv('POLL_INTERVAL','10'))); DELAY=int(os.getenv('INCREASE_DELAY','60'))
NETS=[ipaddress.ip_network(x.strip()) for x in os.getenv('LOCAL_NETWORKS','192.168.0.0/16,10.0.0.0/8,172.16.0.0/12').split(',')]
L={0:ef('QBIT_LIMIT_0_STREAMS_MIB','4'),1:ef('QBIT_LIMIT_1_STREAM_MIB','2'),2:ef('QBIT_LIMIT_2_STREAMS_MIB','1')}; L3=ef('QBIT_LIMIT_3PLUS_STREAMS_MIB','.5')
s=requests.Session();s.headers['X-Emby-Token']=KEY
def ipof(v):
 if not v:return None
 if v.startswith('['):v=v[1:v.index(']')]
 elif v.count(':')==1:v=v.rsplit(':',1)[0]
 try:return ipaddress.ip_address(v)
 except:return None
def count():
 r=s.get(JF+'/Sessions',timeout=7);r.raise_for_status();n=0
 for x in r.json():
  if not x.get('NowPlayingItem') or x.get('PlayState',{}).get('IsPaused'):continue
  ip=ipof(x.get('RemoteEndPoint'))
  if ip is not None and any(ip in z for z in NETS):continue
  n+=1
 return n
def conn():
 c=qbittorrentapi.Client(host=os.getenv('QBIT_HOST','gluetun'),port=int(os.getenv('QBIT_PORT','8080')),username=os.environ['QBIT_USERNAME'],password=os.environ['QBIT_PASSWORD']);c.auth_log_in();return c
def limit(n):return L3 if n>=3 else L[n]
def setlim(c,m):
 b=int(m*1024**2)
 if BANDWIDTH_DRY_RUN: logging.info('DRY RUN: would set qBit %.2f MiB/s',m);return
 if int(c.transfer_upload_limit())!=b:c.transfer_set_upload_limit(limit=b);logging.info('qBit %.2f MiB/s',m)
c=None;ap=None;pending=None;since=0
while True:
 try:
  if c is None:c=conn()
  n=count()
  if ap is None or n>ap:setlim(c,limit(n));ap=n;pending=None
  elif n<ap:
   if pending!=n:pending=n;since=time.monotonic()
   elif time.monotonic()-since>=DELAY and count()==n:setlim(c,limit(n));ap=n;pending=None
  else:pending=None
  time.sleep(POLL)
 except Exception as e:logging.error(e);c=None;time.sleep(POLL)
