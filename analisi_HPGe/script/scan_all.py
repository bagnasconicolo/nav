import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from fit2 import *; from libs import *; from libfit import g
k=sys.argv[1] if len(sys.argv)>1 else 'TR'; c,lt,_,_=load(k); lib=TR_LIB if k=='TR' else LA_LIB
lib_full=lib+[(26.34,'Am-241',2.31),(92.6,'Th-234 (92.4+92.8)',0),(209.25,'Ac-228',3.9),(270.25,'Ac-228',3.5),(328.0,'Ac-228',2.9),(409.5,'Ac-228',1.9),(463.0,'Ac-228',4.4),(794.9,'Ac-228',4.3),(835.7,'Ac-228',1.6),(1630.6,'Ac-228',1.5),(1729.6,'Bi-214',2.9),(1847.4,'Bi-214',2.0),(1408.0,'Eu-152',0),(1401.5,'Bi-214',1.3),(1509.2,'Bi-214',2.1),(665.4,'Bi-214',1.5),(806.2,'Bi-214',1.3),(1155.2,'Bi-214',1.6),(1280.96,'Bi-214',1.4),(53.2,'Pb-214',1.1),(77.1,'Bi Ka1',0),(74.8,'Bi Ka2',0)]
known=np.array([l[0] for l in lib_full]); names=[l[1] for l in lib_full]
sig=[]
for i in range(8,2030):
    e=np.polyval(cE,i); x=np.arange(i-6,i+7).astype(float); y=c[max(i-6,0):i+7]; x=x[-len(y):]
    M=np.array([np.ones_like(x),x-i,g(x,i,sig_ch(max(e,20)))]).T; w=np.maximum(y,1.)
    for it in range(3):
        A=M.T@(M/w[:,None]); p=np.linalg.solve(A,M.T@(y/w)); w=np.maximum(M@p,.5)
    sig.append((p[2]/np.sqrt(np.linalg.inv(A)[2,2]),e,p[2]))
sig=np.array(sig)
print(f"{'E (keV)':>8} {'N':>7} {'sigma':>6}  assegnazione")
for j in range(1,len(sig)-1):
    s,e,a=sig[j]
    if s>4 and s>=sig[j-1,0] and s>=sig[j+1,0]:
        d=np.abs(known-e); m=np.argsort(d)[:2]
        lab=' / '.join(f"{names[q]} {known[q]:.1f}" for q in m if d[q]<2.0) or '*** NON IDENTIFICATO ***'
        print(f"{e:8.1f} {a:7.0f} {s:6.1f}  {lab}")
