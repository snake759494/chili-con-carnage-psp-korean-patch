"""Full build: python tools/build.py OUT.iso"""
import sys,os,glob,struct
sys.path.insert(0,os.path.dirname(__file__))
import naz,loctext,isonaz,font,imgpatch
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
KO=os.path.join(ROOT,'translation','ko')

def load_ko():
    T={}
    for fn in glob.glob(os.path.join(KO,'*.txt')):
        m={}
        for line in open(fn,encoding='utf-8').read().splitlines():
            if not line.strip(): continue
            i,t=line.split('\t',1);m[int(i)]=t
        T[os.path.basename(fn)[:-4]]=m
    return T

def patch_text(d,T,used,hdr=0x14):
    for bi in range(len(loctext.find_blocks(d))):
        b=loctext.find_blocks(d)[bi]
        bn=b['name'].split('/')[-1][:-4]
        if bn not in T: continue
        s,o,c,a=loctext.decode_block(d,b)
        slots=[x if x and x[0] else [] for x in s]
        k=0
        for si,sl in enumerate(slots):
            if not sl: continue
            if k in T[bn]:
                t=T[bn][k]
                assert len(sl)==2,(bn,k,sl)
                slots[si]=[sl[0],t];used.update(t)
            k+=1
        d=loctext.rebuild_block(d,b,slots,hdr_size_field=hdr)
    return d

def main(out):
    T=load_ko();used=set();rep={}
    hs=sorted({c for m in T.values() for t in m.values() for c in t if 0xAC00<=ord(c)<=0xD7A3})
    MAP={c:chr(0x0400+(i//94)*0x100+0xA1+i%94) for i,c in enumerate(hs)}
    for m in T.values():
        for k in m: m[k]=''.join(MAP.get(c,c) for c in m[k])
    for e in naz.entries():
        nm=e['name']
        if '/uk/' in nm and '/maps/' in nm:
            d=naz.read(nm)
            if b'/data/Localize/' not in d: continue
            nd=patch_text(d,T,used,d.find(bytes.fromhex('fa4ea20dd433625e69334027'))+0x14)
            if nd!=d: rep[nm]=nd
    hang={c:MAP[c] for c in hs}
    sm='data_psp/maps/todpsp_the_game/todpsp_game/shared/todpsp_game.main'
    keep=set(MAP.values())|set('½∞…™®©°')
    for e in naz.entries():
        if '/uk/' in e['name'] and '/maps/' in e['name']:
            dd=naz.read(e['name'])
            for b in loctext.find_blocks(dd):
                for x in loctext.decode_block(dd,b)[0]:
                    for p in x: keep.update(p)
    rep[sm]=font.build(naz.read(sm),hang,None)
    rep.update(imgpatch.build_all(naz.read))
    print('files',len(rep))
    print('naz',isonaz.build(out,rep))

if __name__=='__main__':
    main(sys.argv[1])
