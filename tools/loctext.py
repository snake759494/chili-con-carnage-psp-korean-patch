"""Localized text blocks inside .main/.map files.
Block = 4 descriptors (16B each: u32 flag, s32 rel(from field), u32 count, u32 cap)
 D0 aux (timecodes f32), D1 u16 slot offsets (998), D2 huffman bitstream (bytes), D3 tree root
Tree node 12B: (0xc, rel_right(from field), junk) internal / (0,0,value) leaf ; left child = next node.
Bits LSB-first, each slot byte aligned, string NUL terminated."""
import struct,re
def rp(d,p): return p+4+struct.unpack_from('<i',d,p+4)[0]
def find_blocks(d):
    out=[]
    for m in re.finditer(rb'/data/Localize/[\x20-\x7e]+?\.txt\x00',d):
        n=m.start()
        # D3 descriptor is right before name with possible 4-byte len field
        for back in (0x10,0x0c):
            q=n-back
            if d[q+1]==0xfa or True:
                pass
        # search back for 4 descriptors of 16 bytes whose last points at tree (after name)
        found=n-0xc
        assert d[found+1]==0xfa
        D=[found-0x30,found-0x20,found-0x10,found]
        out.append(dict(name=m.group()[:-1].decode(),D=D,name_pos=n))
    return out
def tree(d,root):
    codes={}
    def walk(p,c):
        t,rel,v=struct.unpack_from('<IiI',d,p)
        if t==0: codes[c]=v&0xffff; return
        walk(p+12,c+'0'); walk(p+4+rel,c+'1')
    walk(root,'');return codes
def decode_block(d,b):
    D0,D1,D2,D3=b['D']
    n1=struct.unpack_from('<I',d,D1+8)[0]; offs=struct.unpack_from('<%dH'%n1,d,rp(d,D1))
    n2=struct.unpack_from('<I',d,D2+8)[0]; bs=d[rp(d,D2):rp(d,D2)+n2]
    codes=tree(d,rp(d,D3))
    strs=[]
    for i,o in enumerate(offs):
        parts=[];s=[];c='';p=o*8
        while p<len(bs)*8 and len(parts)<2:
            c+='1' if (bs[p>>3]>>(p&7))&1 else '0';p+=1
            if c in codes:
                v=codes[c];c=''
                if v==0: parts.append(''.join(chr(x) for x in s));s=[]
                else: s.append(v)
                if len(parts)==1 and parts[0]=='': break
        strs.append(parts)
    n0=struct.unpack_from('<I',d,D0+8)[0]
    aux=struct.unpack_from('<%df'%n0,d,rp(d,D0)) if 0<n0<10000 else ()
    return strs,offs,codes,aux

import heapq
def build_tree(freq):
    h=[(f,i,('L',v)) for i,(v,f) in enumerate(sorted(freq.items()))]
    heapq.heapify(h);k=len(h)
    if len(h)==1: heapq.heappush(h,(0,k,('L',0xffff)));k+=1
    while len(h)>1:
        a=heapq.heappop(h);b=heapq.heappop(h)
        heapq.heappush(h,(a[0]+b[0],k,('N',a[2],b[2])));k+=1
    return h[0][2]
def serialize_tree(t,base):
    """returns bytes, codes; base = absolute file position of root"""
    out=bytearray();codes={}
    def emit(n,c):
        p=len(out);out.extend(b'\0'*12)
        if n[0]=='L':
            struct.pack_into('<III',out,p,0,0,n[1]);codes[n[1]]=c;return
        emit(n[1],c+'0');r=len(out);emit(n[2],c+'1')
        struct.pack_into('<IiI',out,p,0xc,r-(p+4),0x0a74)
    emit(t,'');return bytes(out),codes
def encode_block(d,b,slots):
    """slots: list(998) of [key,value] or []. returns new file bytes with data appended."""
    D0,D1,D2,D3=b['D']
    n1=struct.unpack_from('<I',d,D1+8)[0]
    assert len(slots)==n1
    freq={0:0}
    for s in slots:
        if not s: freq[0]+=1;continue
        for part in s:
            for ch in part: freq[ord(ch)]=freq.get(ord(ch),0)+1
            freq[0]+=1
    t=build_tree(freq)
    d=bytearray(d)
    while len(d)%4: d.append(0)
    tpos=len(d);tb,codes=serialize_tree(t,tpos);d+=tb
    bits=[];offs=[]
    for s in slots:
        while len(bits)%8: bits.append('0')
        offs.append(len(bits)//8)
        seq=[0] if not s else [x for part in s for x in [ord(c) for c in part]+[0]]
        for v in seq: bits.extend(codes[v])
    while len(bits)%8: bits.append('0')
    bs=bytearray(len(bits)//8)
    for i,bt in enumerate(bits):
        if bt=='1': bs[i>>3]|=1<<(i&7)
    assert max(offs)<65536,'offset overflow'
    bpos=len(d);d+=bs
    while len(d)%4: d.append(0)
    opos=len(d);d+=struct.pack('<%dH'%n1,*offs)
    while len(d)%4: d.append(0)
    def setp(D,pos,cnt=None):
        struct.pack_into('<i',d,D+4,pos-(D+4))
        if cnt is not None: struct.pack_into('<II',d,D+8,cnt,cnt)
    setp(D1,opos);setp(D2,bpos,len(bs));setp(D3,tpos)
    return bytes(d)

def tree_end(d,root):
    mx=[root]
    def walk(p):
        mx[0]=max(mx[0],p+12)
        t,rel,v=struct.unpack_from('<IiI',d,p)
        if t==0: return
        walk(p+12); walk(p+4+rel)
    walk(root);return mx[0]
def rebuild_block(d,b,slots,hdr_size_field=0x14,keep_size=False):
    """Rebuild text object in place (64-byte object alignment kept); shift rest of file."""
    D1=b['D'][1]
    n1=struct.unpack_from('<I',d,D1+8)[0];assert len(slots)==n1
    freq={0:0}
    for s in slots:
        if not s: freq[0]+=1;continue
        for part in s:
            for ch in part: freq[ord(ch)]=freq.get(ord(ch),0)+1
            freq[0]+=1
    tb,codes=serialize_tree(build_tree(freq),0)
    bits=[];offs=[]
    for s in slots:
        while len(bits)%8: bits.append('0')
        offs.append(len(bits)//8)
        seq=[0] if not s else [x for part in s for x in [ord(c) for c in part]+[0]]
        for v in seq: bits.extend(codes[v])
    while len(bits)%8: bits.append('0')
    bs=bytearray(len(bits)//8)
    for i,bt in enumerate(bits):
        if bt=='1': bs[i>>3]|=1<<(i&7)
    assert max(offs)<65536,'offset overflow'
    return rebuild_raw(d,b,tb,bytes(bs),offs,hdr_size_field,keep_size)

def rebuild_raw(d,b,tb,bs,offs,hdr_size_field=0x14,keep_size=False):
    D0,D1,D2,D3=b['D']
    n1=struct.unpack_from('<I',d,D1+8)[0];n0=struct.unpack_from('<I',d,D0+8)[0]
    troot=rp(d,D3);aux=d[rp(d,D0):rp(d,D0)+n0*8] if n0 else b''
    old_off_end=rp(d,D1)+n1*2
    ph=(D0-0x2c)%0x40
    al=lambda x:x+((ph-x)%0x40)
    nxt=al(old_off_end)
    pass  # alignment padding may hold junk
    head=bytearray(d[:troot])
    body=bytearray(tb)
    while (troot+len(body)-D0)%4: body.append(0)
    ds=troot+len(body)
    body+=aux;bpos=troot+len(body);body+=bs
    while (troot+len(body)-D0)%4: body.append(0)
    opos=troot+len(body);body+=struct.pack('<%dH'%n1,*offs)
    newend=troot+len(body)
    nn=al(newend)
    if keep_size:
        assert newend<=old_off_end,'does not fit %d'%(newend-old_off_end)
        nn=nxt
    nd=head+body+bytes(nn-newend)+d[nxt:]
    delta=len(nd)-len(d)
    def setp(D,pos,cnt=None):
        struct.pack_into('<i',nd,D+4,pos-(D+4))
        if cnt is not None: struct.pack_into('<II',nd,D+8,cnt,cnt)
    struct.pack_into('<i',nd,D0-0xc,ds-(D0-0xc))
    setp(D0,ds);setp(D2,bpos,len(bs));setp(D1,opos);setp(D3,troot)
    if hdr_size_field is not None:
        struct.pack_into('<I',nd,hdr_size_field,struct.unpack_from('<I',nd,hdr_size_field)[0]+delta)
    return bytes(nd)
