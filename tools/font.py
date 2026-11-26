"""Rebuild ODMidText_24 (+Stroke3) fonts in shared/todpsp_game.main with Hangul glyphs.
Both fonts are rebuilt into 512x512 textures (main CLUT8, stroke CLUT4) at uniform scale S;
glyph record keeps screen width w, texture extents use the new normalized u/v/uw."""
import struct,os,sys
import numpy as np
from PIL import Image,ImageFont,ImageDraw,ImageFilter
sys.path.insert(0,os.path.dirname(__file__))
from swz import unswizzle,swizzle
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
KFONT=os.path.join(ROOT,'NanumSquareNeo-cBd.ttf')
CELL=29          # original row height (texels)
SHEAR=0.08
KSIZE=26;KBASE=23
ADV=float(__import__('os').environ.get('FONT_ADV','1'))
TW=int(__import__('os').environ.get('FONT_TW','512'));TH=512

class FontObj:
    def __init__(s,d,name):
        n=d.find(name.encode()+b'\0');assert n>0
        s.start=n-0x28                       # object start (type field)
        s.gdesc=n+0x64                        # glyph descriptor (flag 0x34)
        assert struct.unpack_from('<I',s.gdesc and d,s.gdesc)[0]==0x34
        s.tex=n+0x98                          # texture header (0x40, relpal, 8, GE...)
        assert struct.unpack_from('<I',d,s.tex)[0]==0x40
        s.ge=s.tex+12
        s.texdata=s.tex+0x40
        s.pal=s.tex+4+struct.unpack_from('<i',d,s.tex+4)[0]
        s.glyphs=s.gdesc+4+struct.unpack_from('<i',d,s.gdesc+4)[0]
        s.n=struct.unpack_from('<I',d,s.gdesc+8)[0]
        s.psm=struct.unpack_from('<I',d,s.ge+8)[0]&0xff   # c3 TPSM
        s.end=s.glyphs+s.n*32
def decode_tex(d,o):
    if o.psm==5:
        raw=unswizzle(d[o.texdata:o.texdata+256*512],256,512)
        idx=np.frombuffer(raw,np.uint8).reshape(512,256)
        pal=np.frombuffer(d[o.pal:o.pal+1024],np.uint8).reshape(256,4)
    else:
        raw=unswizzle(d[o.texdata:o.texdata+128*512],128,512)
        b=np.frombuffer(raw,np.uint8).reshape(512,128)
        idx=np.zeros((512,256),np.uint8);idx[:,0::2]=b&15;idx[:,1::2]=b>>4
        pal=np.frombuffer(d[o.pal:o.pal+64],np.uint8).reshape(16,4)
    return pal[idx].astype(np.float32),pal

def render_hangul(ch,font):
    """returns (alpha float32 array CELL x w, advance w) at original resolution"""
    k=4
    W=40*k;img=Image.new('L',(W,CELL*k),0);dr=ImageDraw.Draw(img)
    dr.text((6*k,KBASE*k),ch,font=font,fill=255,anchor='ls')
    a=np.asarray(img,np.float32)
    # shear: shift rows right proportional to height above baseline
    out=np.zeros_like(a);base=KBASE*k
    for y in range(a.shape[0]):
        sh=int(round(SHEAR*(base-y)))
        if sh>=0: out[y,sh:]=a[y,:W-sh]
        else: out[y,:W+sh]=a[y,-sh:]
    cols=np.where(out.max(0)>0)[0]
    x0=max(cols.min()-1*k,0);x1=cols.max()+1*k
    out=out[:,x0:x1]
    w=int(round(out.shape[1]/k))
    return out,w
    im=Image.fromarray(out.astype(np.uint8)).resize((w,CELL),Image.LANCZOS)
    return np.asarray(im,np.float32),w

def dilate(a,r):
    im=Image.fromarray(np.clip(a,0,255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MaxFilter(2*r+1)),np.float32)

def scale_rgba(arr,w,h):
    # premultiplied resize
    a=arr[:,:,3:4]/255.0;pm=np.concatenate([arr[:,:,:3]*a,arr[:,:,3:4]],2)
    chans=[np.asarray(Image.fromarray(pm[:,:,i].astype(np.float32),'F').resize((w,h),Image.LANCZOS)) for i in range(4)]
    o=np.stack(chans,2);al=np.clip(o[:,:,3:4],0,255)
    rgb=np.where(al>0.5,o[:,:,:3]/np.maximum(al,1e-3)*255.0,255.0)
    return np.concatenate([np.clip(rgb,0,255),al],2)

def quantize(arr,pal,weights=(1,1,1,2)):
    p=pal.astype(np.float32);wt=np.array(weights,np.float32)
    flat=arr.reshape(-1,4)
    # treat fully transparent as alpha-only match
    out=np.empty(len(flat),np.uint8)
    for i in range(0,len(flat),65536):
        c=flat[i:i+65536]
        dd=(((c[:,None,:]-p[None,:,:])**2)*wt).sum(2)
        out[i:i+65536]=dd.argmin(1)
    return out.reshape(arr.shape[:2])

def pack(sizes,H):
    """shelf pack list of widths into 512x512 rows of height H(+1). returns positions or None"""
    pos=[];x=0;y=0
    for w in sizes:
        if x+w>TW: x=0;y+=H+1
        if y+H>TH: return None
        pos.append((x,y));x+=w+1
    return pos

def build(d,chars,keep=None):
    """d: shared main bytes (no prefix). chars: iterable of extra chars (hangul). returns new bytes"""
    m=FontObj(d,'/data/Fonts/ODMidText_24.font');st=FontObj(d,'/data/Fonts/ODMidText_24_Stroke3.font')
    assert m.n==st.n
    mt,mpal=decode_tex(d,m);stt,spal=decode_tex(d,st)
    recs=[];imgs=[]
    have=set()
    for i in range(m.n):
        r=list(struct.unpack_from('<HHIfffffI',d,m.glyphs+i*32))
        rs=struct.unpack_from('<HHIfffffI',d,st.glyphs+i*32);assert rs[0]==r[0]
        x=int(round(r[5]*256));y=int(round(r[6]*512));tw=int(round(r[7]*256))
        imgs.append((mt[y:y+CELL,x:x+tw],stt[y:y+CELL,x:x+tw],1))
        if keep is not None and chr(r[0]) not in keep and r[0]>0x7e: imgs.pop();continue
        recs.append(r);have.add(r[0])
    font=ImageFont.truetype(KFONT,KSIZE*4)
    font2=ImageFont.truetype(os.path.join(ROOT,'NanumSquareNeo-bRg.ttf'),KSIZE*4)
    def dbl(ch):  # double consonant (initial or final): lighter weight + wider so gaps survive small sizes
        c=ord(ch)-0xAC00
        return 0<=c<11172 and (c//588 in (1,4,8,10,13) or c%28 in (2,20))
    tmpl=list(recs[[chr(r[0]) for r in recs].index('H')])
    items=sorted(chars.items(),key=lambda x:x[1]) if isinstance(chars,dict) else [(c,c) for c in sorted(set(chars))]
    for ch,code in items:
        if ord(code) in have: continue
        if dbl(ch):
            a,w=render_hangul(ch,font2);nw=int(round(a.shape[1]*1.2))
            a=np.asarray(Image.fromarray(a).resize((nw,a.shape[0]),Image.LANCZOS),np.float32);w=int(round(w*1.2))
        else: a,w=render_hangul(ch,font)
        hh,ww=a.shape
        mr=np.zeros((hh,ww,4),np.float32);mr[:,:,:3]=255;mr[:,:,3]=a
        sa=dilate(a,12);sr=np.zeros((hh,ww,4),np.float32);sr[:,:,:3]=255;sr[:,:,3]=sa
        r=list(tmpl);r[0]=ord(code);r[4]=float(w);r[8]=0
        recs.append(r);imgs.append((mr,sr,4))
    # choose scale
    for S in [x/100 for x in range(100,30,-1)]:
        H=int(round(CELL*S));ws=[max(1,int(round(im[0].shape[1]*S/im[2]))) for im in imgs]
        pos=pack(ws,H)
        if pos: break
    print('font scale',S,'cell',H,'glyphs',len(recs))
    M=np.zeros((TH,TW,4),np.float32);M[:,:,:3]=255
    SS=np.zeros((TH,TW,4),np.float32);SS[:,:,:3]=255
    for (mi,si,kk),(x,y),w in zip(imgs,pos,ws):
        M[y:y+H,x:x+w]=scale_rgba(mi,w,H)
        SS[y:y+H,x:x+w]=scale_rgba(si,w,H)
    Mi=quantize(M,mpal);Si=quantize(SS,spal)
    mtex=swizzle(Mi.tobytes(),TW,TH)
    sb=(Si[:,0::2]|(Si[:,1::2]<<4)).astype(np.uint8)
    stex=swizzle(sb.tobytes(),TW//2,TH)
    def grecs(base_recs):
        out=bytearray()
        for r,(x,y),w in zip(base_recs,pos,ws):
            rr=list(r);rr[4]=round(w/S*(0.88 if 0x400<=r[0]<0xc00 else 1.0),2);rr[5]=x/256;rr[6]=y/TH;rr[7]=w/256
            out+=struct.pack('<HHIfffffI',*rr)
        for r in base_recs[len(pos):]: out+=struct.pack('<HHIfffffI',*r)
        return bytes(out)
    sm={struct.unpack_from('<H',d,st.glyphs+i*32)[0]:list(struct.unpack_from('<HHIfffffI',d,st.glyphs+i*32)) for i in range(st.n)}
    srecs=[sm.get(r[0],list(r)) for r in recs]
    mg=grecs(recs);sg=grecs(srecs)
    vh=H/TH
    # assemble: process later object first (stroke) so earlier offsets stay valid
    nd=bytearray(d);delta_total=0
    for o,tex,pal,g in ((st,stex,spal,sg),(m,mtex,mpal,mg)):
        ph=o.start%0x40
        al=lambda x:x+((ph-x)%0x40)
        old_next=al(o.end)
        assert not any(nd[o.end:old_next])
        body=bytearray(nd[o.start:o.texdata])
        # header fields inside body (relative to object start)
        off=lambda p:p-o.start
        body+=tex
        palpos=len(body);body+=pal.tobytes()
        gpos=len(body);body+=g
        endpos=o.start+len(body);newnext=al(endpos)
        body+=bytes(newnext-endpos)
        struct.pack_into('<i',body,off(o.tex+4),palpos-off(o.tex+4))
        struct.pack_into('<i',body,off(o.gdesc+4),gpos-off(o.gdesc+4))
        n=len(g)//32;struct.pack_into('<II',body,off(o.gdesc+8),n,n)
        # GE: TBW (a8) and TSIZE (b8)
        for k in range(12):
            p=off(o.ge)+k*4;cmd=body[p+3]
            v=struct.unpack_from('<I',body,p)[0]
            if cmd==0xa8: struct.pack_into('<I',body,p,(v&0xff000000)|(v&0x00ff0000)|TW)
            if cmd==0x98: struct.pack_into('<I',body,p,(v&0xffff0000)|(len(tex)//128))
            if cmd==0xb8: struct.pack_into('<I',body,p,0xb8000900|(TW.bit_length()-1))
        # v-height float (header +0x2c from name start): find 0x3d680000
        vp=body.find(struct.pack('<f',CELL/512.0),0,0x80)
        assert vp>0
        struct.pack_into('<f',body,vp,vh)
        import os as _o
        if _o.environ.get('FONT_SC')=='1': struct.pack_into('<ff',body,vp-8,1/S,1/S)
        if _o.environ.get('FONT_SC')=='2': struct.pack_into('<ff',body,vp+0x38,1/S,1/S)
        delta=len(body)-(old_next-o.start)
        nd=nd[:o.start]+body+nd[old_next:]
        delta_total+=delta
    struct.pack_into('<I',nd,0x14,struct.unpack_from('<I',nd,0x14)[0]+delta_total)
    print('font delta',delta_total)
    Image.fromarray(np.concatenate([M,SS],1).astype(np.uint8),'RGBA').save(os.path.join(ROOT,'work','font_new.png'))
    return bytes(nd)
