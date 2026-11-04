import sys; sys.path.insert(0,'.')
from fit2 import *; from libs import *
from libfit import g
for k,lib in [('TR',TR_LIB),('La',LA_LIB)]:
    c,lt,_,_=load(k); known=np.array([l[0] for l in lib])
    print('====',k); prev=-10
    sigs=[]
    for i in range(32,2030):
        e=np.polyval(cE,i)
        x=np.arange(i-6,i+7).astype(float); y=c[i-6:i+7]
        M=np.array([np.ones_like(x),x-i,g(x,i,sig_ch(e))]).T; w=np.maximum(y,1.)
        for it in range(3):
            A=M.T@(M/w[:,None]); p=np.linalg.solve(A,M.T@(y/w)); w=np.maximum(M@p,.5)
        sigs.append((p[2]/np.sqrt(np.linalg.inv(A)[2,2]),e,p[2]))
    sigs=np.array(sigs)
    for j in range(1,len(sigs)-1):
        s,e,a=sigs[j]
        if s>4 and s>=sigs[j-1,0] and s>=sigs[j+1,0]:
            d=np.min(np.abs(known-e))
            if d>1.6: print(f"  UNIDENTIFIED? {e:8.2f} keV  N={a:7.0f} {s:5.1f} sigma (nearest lib {known[np.argmin(np.abs(known-e))]:.2f})")
