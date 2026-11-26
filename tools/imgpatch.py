"""Korean text on 512x272 RGBA8888 textures (bootscreen, concept art).
Every position/size below was measured on the original texture (see docs/TECHNICAL.md)."""
import os,sys
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,os.path.dirname(__file__))
from swz import unswizzle,swizzle
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
W,H=512,272
P='data_psp/textures/'
def load(d):
    off=len(d)-W*H*4
    return off,np.frombuffer(unswizzle(d[off:],W*4,H),np.uint8).reshape(H,W,4).copy()
def store(d,off,img): return d[:off]+swizzle(np.ascontiguousarray(img).tobytes(),W*4,H)
def font(name,size): return ImageFont.truetype(os.path.join(ROOT,name),size)

# ---------------- bootscreen ----------------
# original lines: yellow fill rows (top,bottom) and ink width, all centred on x=240.
# Korean keeps the same rows/height and centre; width never exceeds the original line
BOOT=[((117,126),411,'칠리 콘 카나지 © 2006 Eidos Interactive Limited. 퍼블리싱:'),
      ((134,143),417,'Eidos Interactive Limited, 2006. 개발: Deadline Games A/S'),
      ((150,160),451,'칠리 콘 카나지, 칠리 콘 카나지 로고, Eidos 및 Eidos 로고는'),
      ((167,176),421,'Eidos Interactive Limited의 상표이며, Deadline Games 및'),
      ((184,193),357,'Deadline Games 로고는 Deadline Games의 상표입니다.'),
      ((201,210),125,'모든 권리 보유.')]
def ink(text,f,k=1):
    im=Image.new('L',(int(f.getlength(text))+40,f.size*2),0)
    ImageDraw.Draw(im).text((20,f.size//2),text,font=f,fill=255)
    a=np.asarray(im);r=np.where(a.any(1))[0];c=np.where(a.any(0))[0]
    return a[r[0]:r[-1]+1,c[0]:c[-1]+1]
def boot(d):
    off,img=load(d);rgb=img[:,:,:3].copy()
    # erase original text: yellow fill + dark outline/shadow inside the text block
    y0,y1,x0,x1=112,216,6,479
    sub=rgb[y0:y1,x0:x1].astype(int)
    yel=(sub[:,:,0]>170)&(sub[:,:,1]>150)&(sub[:,:,2]<140)
    m=np.zeros((H,W),np.uint8);m[y0:y1,x0:x1][yel]=255
    near=cv2.dilate(m,np.ones((9,9),np.uint8))
    dark=(rgb.astype(int).sum(2)<260).astype(np.uint8)*255
    m=cv2.dilate(m|(dark&near),np.ones((3,3),np.uint8))
    rgb=cv2.cvtColor(cv2.inpaint(cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),m,6,cv2.INPAINT_TELEA),cv2.COLOR_BGR2RGB)
    k=4;f=font('NanumSquareNeo-cBd.ttf',15*k)
    fill=np.zeros((H*k,W*k),np.float32)
    for (t,b),w,text in BOOT:
        # height = original fill height; width = original ink width, reached by a mild
        # horizontal scale (<=1.15) plus even letter spacing instead of stretching glyphs
        a=ink(text,f).astype(np.float32);th=(b-t+1)*k;sy=th/a.shape[0]
        nat=a.shape[1]*sy;sx=min(w*k/nat,1.25)*sy
        gl=[];x=0.0
        for ch in text:
            adv=f.getlength(ch)*sx
            if ch!=' ':
                g=Image.new('L',(int(f.size*2),f.size*2),0);ImageDraw.Draw(g).text((f.size//2,f.size//2),ch,font=f,fill=255)
                gl.append((x,np.asarray(g)))
            x+=adv
        # ink rows of whole line (to place glyph rows consistently)
        full=Image.new('L',(int(f.getlength(text))+40,f.size*2),0);ImageDraw.Draw(full).text((20,f.size//2),text,font=f,fill=255)
        fr=np.where(np.asarray(full).any(1))[0];r0,r1=fr[0],fr[-1]
        # measure ink extent with zero tracking, then spread the rest across gaps
        def place(track):
            canvas=np.zeros((th,int(x+track*len(text))+8*k),np.float32);cx=0.0;i=0
            for ch in text:
                if ch!=' ':
                    g=gl[i][1][r0:r1+1];i+=1
                    c=np.where(g.any(0))[0]
                    gg=cv2.resize(g.astype(np.float32),(max(1,int(round(g.shape[1]*sx))),th),interpolation=cv2.INTER_AREA)
                    xo=int(round(cx));ww=min(gg.shape[1],canvas.shape[1]-xo)
                    canvas[:,xo:xo+ww]=np.maximum(canvas[:,xo:xo+ww],gg[:,:ww])
                cx+=f.getlength(ch)*sx+track
            cc=np.where(canvas.any(0))[0];return canvas[:,cc[0]:cc[-1]+1]
        c0=place(0);gaps=len(text)-1
        a=place(min(1.0*k,max(0.0,(w*k-c0.shape[1])/gaps)))   # at most 1px extra spacing
        if a.shape[1]>w*k: a=cv2.resize(a,(w*k,th),interpolation=cv2.INTER_AREA)
        tw=a.shape[1]
        x=(240*k)-tw//2;fill[t*k:t*k+th,x:x+tw]=np.maximum(fill[t*k:t*k+th,x:x+tw],a)
    fm=fill/255
    ol=cv2.dilate(fm,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(2*int(1.6*k)+1,)*2))
    sh=np.zeros_like(ol);sh[2*k:,1*k:]=ol[:-2*k,:-1*k]          # drop shadow (1,2) like original
    dark=np.maximum(ol,sh)
    def down(x): return cv2.resize(x,(W,H),interpolation=cv2.INTER_AREA)[:,:,None]
    fm,dark=down(fm),down(dark)
    out=rgb.astype(np.float32)*(1-dark)+np.array([10,6,0],np.float32)*dark
    out=out*(1-fm)+np.array([255,222,40],np.float32)*fm
    img[:,:,:3]=np.clip(out,0,255).astype(np.uint8)
    return store(d,off,img),img

# ---------------- concept art ----------------
G7=('Galmuri7.ttf',8);G9=('Galmuri9.ttf',10)
# labels: (original ink box x0,y0,x1,y1 [cap region], Korean)
LABELS={
 'concept_lostoros02':[((33,30,119,39),'빨랫줄'),((232,30,278,39),'짚라인'),((360,30,446,39),'닭장'),
                       ((167,253,192,262),'경사로'),((298,252,391,262),'유리 채광창')],
 'concept_lostoros03':[((337,17,407,26),'비상계단'),((167,235,232,245),'트램펄린'),((341,237,412,246),'타고 넘는 울타리')],
}
# storyboard caption cells (inner box, first text line top) -> lines [(speaker, text)]
BOARDS={
 'concept_musclebabe':[
  ((20,90,165,135),[('라미로','너희 개자식들을 아무리 쓰러뜨려도 아버지 복수를 끝내지 못하는 놈이지.'),('엘베스','에르네스토의 아들?')]),
  ((168,90,314,135),[('엘베스','맙소사! 모랄레스한테 무슨 짓을 한 거야?'),('라미로','갑자기 숨을 안 쉬더라고!')]),
  ((317,90,462,135),[('엘베스','안돼애애! 등 뒤 조심해라, 애송이. 내가 널 찾아낼 거다. 찾기만 하면 미사일을 네 놈…')]),
  ((20,222,165,267),[('엘베스','…똥구멍에!'),('라미로','뭘 어쩌겠다고?')]),
  ((168,222,314,267),[('엘베스','아냐 아냐 아니라고! 난 여자가 좋아! 똑똑히 기억해 둬…')]),
  ((317,222,462,267),[('엘베스','…여자 말이야! 여자! …끊는다.')])],
 'concept_puertoindustrial03':[
  ((21,90,167,135),[('마르코','소문에 세자르 모랄레스가 화물선에 타고 있대. 그 배가 정박한 곳은…')]),
  ((169,90,315,135),[('마르코','…항구야. 가서 배를 산산조각 내 버리자고.')]),
  ((317,90,464,135),[('라미로','그냥 그놈을 찾아서 쏘는 게 더 쉽지 않아?')]),
  ((21,222,167,266),[('마르코','아니! 이건 좋은 계획이야. 난 머리가 좋거든…')]),
  ((169,222,315,266),[('마르코','…알잖아!'),('라미로','그래서 어떻게…')]),
  ((317,222,464,266),[('라미로','…이 배를 날리는데?'),('마르코','뒷좌석에 폭탄이 있거든!')])],
}
def text_mask(a,box,thr=235):
    x0,y0,x1,y1=box;s=a[y0:y1,x0:x1,:3].astype(int)
    m=(s.mean(2)<thr)|(np.abs(s[:,:,0]-s[:,:,1])>30)|(np.abs(s[:,:,1]-s[:,:,2])>30)
    m[m.mean(1)>0.6,:]=False;m[:,m.mean(0)>0.6]=False   # keep cell borders
    return m
def bw_text(text,fspec):
    f=font(*fspec);im=Image.new('1',(int(f.getlength(text))+8,fspec[1]*3),0);dr=ImageDraw.Draw(im)
    dr.fontmode='1';dr.text((2,fspec[1]),text,font=f,fill=1)
    return np.asarray(im,bool),fspec[1]   # baseline-ish origin row = fspec[1]
def glyph_box(fspec):
    m,_=bw_text('가힣',fspec);r=np.where(m.any(1))[0];return r[0],r[-1]
def put(img,m,x,y,color):
    h,w=m.shape;sub=img[y:y+h,x:x+w,:3];sub[m[:sub.shape[0],:sub.shape[1]]]=color
def concept(name,d):
    off,img=load(d);a=img
    for (x0,y0,x1,y1),ko in LABELS.get(name,[]):
        a[y0-1:y1+2,x0-1:x1+2,:3]=255
        m,_=bw_text(ko,G9);c=np.where(m.any(0))[0];m=m[:,c[0]:c[-1]+1]
        gt,gb=glyph_box(G9)
        cx=(x0+x1+1)//2;cy=(y0+y1+1)/2
        put(a,m,cx-m.shape[1]//2,int(round(cy-(gt+gb+1)/2)),(40,40,40))
    for (x0,y0,x1,y1),lines in BOARDS.get(name,[]):
        sub=a[y0:y1,x0:x1,:3].astype(int).mean(2)<110          # cell borders: dark full-length lines
        keep=np.zeros_like(sub);keep[sub.mean(1)>0.9,:]=True;keep[:,sub.mean(0)>0.9]=True
        a[y0:y1,x0:x1,:3][~keep]=255
        gt,gb=glyph_box(G7);pitch=10;tx=x0+1;y=y0+3;maxw=x1-x0-3
        for spk,txt in lines:
            words=(spk+': '+txt).split(' ');cur='';rows=[]
            for wd in words:
                t2=(cur+' '+wd) if cur else wd
                if bw_text(t2,G7)[0].any(0).nonzero()[0].max()-2>maxw and cur: rows.append(cur);cur=wd
                else: cur=t2
            rows.append(cur)
            for i,r in enumerate(rows):
                m,_=bw_text(r,G7);ty=y-gt
                put(a,m,tx-2,ty,(20,20,20))
                if i==0:   # speaker name bold + underline like original
                    n,_=bw_text(spk,G7)
                    cols=np.where(n.any(0))[0];a[y+gb-gt+2,tx-2+cols[0]:tx-2+cols[-1]+1,:3]=20
                y+=pitch
    return store(d,off,a),a
def build_all(read):
    rep={};prev={}
    nm=P+'menu/loadscreens/generated/bootscreen.texture_psp'
    rep[nm],prev['bootscreen']=boot(read(nm))
    for n in list(LABELS)+list(BOARDS):
        p=P+'trophies/generated/%s.texture_psp'%n
        rep[p],prev[n]=concept(n,read(p))
    os.makedirs(os.path.join(ROOT,'work','imgprev'),exist_ok=True)
    for k,v in prev.items(): Image.fromarray(v[:,:,:3]).save(os.path.join(ROOT,'work','imgprev',k+'.png'))
    return rep
if __name__=='__main__':
    import naz;build_all(naz.read)
