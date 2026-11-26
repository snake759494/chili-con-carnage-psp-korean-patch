import glob,os,re,sys
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
bad=0
for fn in glob.glob(ROOT+'/translation/ko/*.txt'):
  bn=os.path.basename(fn);src={}
  for l in open(ROOT+'/translation/src/'+bn,encoding='utf-8').read().split('\n'):
    if not l: continue
    p=(l.split('\t',2)+['',''])[:3];src[int(p[0])]=p[2]
  for l in open(fn,encoding='utf-8').read().splitlines():
    i,t=l.split('\t',1);e=src[int(i)]
    for pat in (r'\n',r'%\d',r'%%','[¢-¿┌∞]'):
      if sorted(re.findall(pat,e))!=sorted(re.findall(pat,t)): print(bn,i,pat,repr(e[:60]),repr(t[:60]));bad+=1
print('bad',bad)
