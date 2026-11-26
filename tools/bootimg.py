"""Korean legal text on bootscreen.texture_psp (512x272 RGBA8888 swizzled, data at end)."""
import os,sys
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont,ImageFilter
sys.path.insert(0,os.path.dirname(__file__))
from swz import unswizzle,swizzle
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
NAME='data_psp/textures/menu/loadscreens/generated/bootscreen.texture_psp'
LINES=['칠리 콘 카나지 © 2006 Eidos Interactive Limited.',
       '퍼블리싱: Eidos Interactive Limited, 2006. 개발: Deadline Games A/S',
       '칠리 콘 카나지, 칠리 콘 카나지 로고, Eidos 및 Eidos 로고는',
       'Eidos Interactive Limited의 상표이며, Deadline Games 및',
       'Deadline Games 로고는 Deadline Games의 상표입니다.',
       'All Rights Reserved.']
def build(d):
    W,H=512,272;off=len(d)-W*H*4
    img=np.frombuffer(unswizzle(d[off:],W*4,H),np.uint8).reshape(H,W,4).copy()
    rgb=img[:,:,:3].copy()
    # mask text (yellow fill + dark outline) in the text box
    y0,y1,x0,x1=108,216,6,478
    sub=rgb[y0:y1,x0:x1].astype(int)
    yel=(sub[:,:,0]>170)&(sub[:,:,1]>150)&(sub[:,:,2]<140)
    m=np.zeros((H,W),np.uint8);m[y0:y1,x0:x1][yel]=255
    near=cv2.dilate(m,np.ones((9,9),np.uint8))
    dark=(rgb.astype(int).sum(2)<260).astype(np.uint8)*255
    m=cv2.dilate(m|(dark&near),np.ones((3,3),np.uint8))
    bgr=cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR)
    out=cv2.inpaint(bgr,m,6,cv2.INPAINT_TELEA)
    rgb=cv2.cvtColor(out,cv2.COLOR_BGR2RGB)
    k=4
    big=Image.fromarray(rgb).resize((W*k,H*k),Image.LANCZOS)
    font=ImageFont.truetype(os.path.join(ROOT,'NanumSquareNeo-cBd.ttf'),13*k)
    dr=ImageDraw.Draw(big)
    y=112*k
    for t in LINES:
        tw=dr.textlength(t,font=font)
        dr.text(((W*k-tw)/2,y),t,font=font,fill=(255,222,40),stroke_width=int(1.6*k),stroke_fill=(10,6,0))
        y+=17*k
    res=np.asarray(big.resize((W,H),Image.LANCZOS))
    img[:,:,:3]=res
    Image.fromarray(img[:,:,:3]).save(os.path.join(ROOT,'work','bootscreen_ko.png'))
    return d[:off]+swizzle(img.tobytes(),W*4,H)
