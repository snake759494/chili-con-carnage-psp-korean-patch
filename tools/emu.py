"""PPSSPP background control: start(iso) / stop() / shot(name) / press(btn)."""
import subprocess,time,os,sys,json,base64
sys.path.insert(0,os.path.dirname(__file__))
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
EXE=os.path.join(ROOT,'work','ppsspp','PPSSPPWindows64.exe')
SHOTS=os.path.join(ROOT,'work','shots')
def ps(cmd): return subprocess.run(['powershell','-NoProfile','-Command',cmd],capture_output=True,text=True).stdout.strip()
def stop():
    ps("Get-Process PPSSPPWindows64 -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq '%s' } | Stop-Process -Force"%EXE)
def pid():
    o=ps("(Get-Process PPSSPPWindows64 -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq '%s' }).Id"%EXE)
    return int(o.split()[0]) if o else None
def port():
    p=pid()
    o=ps("(Get-NetTCPConnection -OwningProcess %d -State Listen -ErrorAction SilentlyContinue).LocalPort"%p)
    return [int(x) for x in o.split()]
def start(iso,wait=25):
    stop();time.sleep(1)
    ps("Start-Process -FilePath '%s' -ArgumentList '\"%s\"' -WindowStyle Hidden"%(EXE,os.path.abspath(iso)))
    time.sleep(wait)
def dbg():
    import websocket
    from ppsspp_rpc import Debugger
    for pt in port():
        try:
            D=Debugger.__new__(Debugger)
            D.w=websocket.create_connection('ws://127.0.0.1:%d/debugger'%pt,subprotocols=['debugger.ppsspp.org'],timeout=15)
            return D
        except Exception: pass
    raise RuntimeError('no debugger port')
def shot(name,d=None):
    os.makedirs(SHOTS,exist_ok=True); d=d or dbg()
    return d.frame(os.path.join(SHOTS,name+'.png'))
def press(btn,d=None,n=1,wait=0.8,dur=4):
    d=d or dbg()
    for _ in range(n): d.call('input.buttons.press',button=btn,duration=dur); time.sleep(wait)
if __name__=='__main__':
    c=sys.argv[1]
    if c=='start': start(sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 25)
    elif c=='stop': stop()
    elif c=='shot': print(shot(sys.argv[2]))
    elif c=='seq':  # seq name btn btn w2 btn ...
        d=dbg()
        for a in sys.argv[3:]:
            if a.startswith('w'): time.sleep(float(a[1:]))
            else: press(a,d)
        print(shot(sys.argv[2],d))
