import struct,sys
P=__import__('os').path.dirname(__file__)+'/../work/iso/PSP_GAME/USRDIR/assets00.naz'
DIR=0x2bec91f1
def rol(b): return bytes(((x<<2)|(x>>6))&0xff for x in b)
def entries(path=P):
    f=open(path,'rb');f.seek(0,2);end=f.tell();f.seek(DIR);d=f.read()
    p=0;out=[]
    while p+0x2e<len(d) and d[p:p+4]==b'\x70\xf3\x06\x04':
        size,size2,nl,fl=struct.unpack_from('<IIHH',d,p+12)
        off=struct.unpack_from('<I',d,p+0x22)[0]
        name=rol(d[p+0x2e:p+0x2e+nl]).decode('latin1')
        out.append(dict(name=name,off=off,size=size,size2=size2,fl=fl,rec=DIR+p))
        p+=0x2e+nl+1
    return out
if __name__=='__main__':
    E=entries();print(len(E))
    for e in E: print(hex(e['off']),e['size'],e['size2'],e['fl'],e['name'])
def read(name,path=P):
    e=[x for x in entries(path) if x['name']==name][0]
    f=open(path,'rb');f.seek(e['off']+len(name)+31);return f.read(e['size'])
