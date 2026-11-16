import os,signal,subprocess,sys,time
children=[]; stopping=False
def on(k,d='true'): return os.getenv(k,d).lower() in ('1','true','yes','on')
def stop(*_):
 global stopping; stopping=True
 for p in children:
  if p.poll() is None:p.terminate()
signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
cmd=[]
if on('RUN_MIGHTYMOUSE'):cmd.append(([sys.executable,'/opt/mightymouse/mightymouse.py'],'/opt/mightymouse'))
if on('RUN_BANDWIDTH_CONTROLLER'):cmd.append(([sys.executable,'/opt/controller/bandwidth_controller.py'],'/opt/controller'))
if on('RUN_STORAGE_GUARD'):cmd.append(([sys.executable,'/opt/controller/storage_guard.py'],'/opt/controller'))
for c,w in cmd: children.append(subprocess.Popen(c,cwd=w))
while not stopping:
 for p in children:
  if p.poll() is not None: print('Child exited; stopping container',flush=True);stop();break
 time.sleep(1)
for p in children:
 if p.poll() is None:
  try:p.wait(10)
  except subprocess.TimeoutExpired:p.kill()
