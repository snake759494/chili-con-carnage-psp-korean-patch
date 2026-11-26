"""Patched ISO: copy original ISO, rewrite assets00.naz keeping physical file order (offsets shift)."""
import os,shutil,struct,sys,re
sys.path.insert(0,os.path.dirname(__file__))
import naz
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
ORIG=os.path.join(ROOT,'Chili Con Carnage (USA).iso')
NAZ_LBN=29344
def build(out_iso,replace):
    import emu,time; emu.stop(); time.sleep(1)
    E=naz.entries()
    f=open(naz.P,'rb');f.seek(naz.DIR);olddir=f.read()
    recs=bytearray(olddir[:-22]);tr=bytearray(olddir[-22:])
    shutil.copyfile(ORIG,out_iso)
    o=open(out_iso,'r+b');base=NAZ_LBN*2048;o.seek(base);pos=0
    for e in sorted(E,key=lambda e:e['off']):
        nl=len(e['name']);f.seek(e['off'])
        prefix=f.read(nl+31)
        nd=replace.get(e['name'])
        if nd is None: nd=f.read(e['size'])
        o.write(prefix+nd+struct.pack('<III',0,len(nd),len(nd)))
        r=e['rec']-naz.DIR
        struct.pack_into('<II',recs,r+12,len(nd),len(nd))
        struct.pack_into('<I',recs,r+0x22,pos)
        pos+=nl+31+len(nd)+12
    struct.pack_into('<I',tr,16,pos)
    o.write(recs);o.write(tr);nazsize=pos+len(recs)+len(tr)
    end=base+nazsize;total=max((end+2047)//2048*2048+7*2048,os.path.getsize(ORIG))
    o.seek(end);o.write(bytes(total-end));o.truncate(total)
    nsec=total//2048
    o.seek(16*2048+80);o.write(struct.pack('<I',nsec)+struct.pack('>I',nsec))
    o.seek(0);head=o.read(NAZ_LBN*2048);n=0
    for m in re.finditer(rb'(?i)assets00[.]naz',head):
        r=m.start()-33
        if r>=0 and struct.unpack_from('<I',head,r+2)[0]==NAZ_LBN:
            o.seek(r+10);o.write(struct.pack('<I',nazsize)+struct.pack('>I',nazsize));n+=1
    assert n>0
    o.close()
    return nazsize
