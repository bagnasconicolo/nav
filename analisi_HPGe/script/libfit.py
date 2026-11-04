import os
import sys; sys.path.insert(0,'.')
from load import *
from lib import LINES
cal=np.load(os.path.join(os.path.dirname(os.path.abspath(__file__)),'cal.npy')); cE=cal[:3]; ab=cal[3:]
def ch_of(e):
    a,b,c=cE; return (-b+np.sqrt(b*b-4*a*(c-e)))/(2*a)
def sig_ch(e): return np.sqrt(np.polyval(ab,e))/2.3548/(2*cE[0]*ch_of(e)+cE[1])
from scipy.special import erf
def g(x,c,s): return 0.5*(erf((x+0.5-c)/(np.sqrt(2)*s))-erf((x-0.5-c)/(np.sqrt(2)*s)))
def fit_group(cnt,energies,half=6):
    chs=np.array([ch_of(e) for e in energies])
    lo=int(np.floor(chs.min()-half)); hi=int(np.ceil(chs.max()+half))+1
    x=np.arange(lo,hi).astype(float); y=cnt[lo:hi]
    M=[np.ones_like(x),x-x.mean()]+[g(x,c,sig_ch(e)) for c,e in zip(chs,energies)]
    M=np.array(M).T; w=np.maximum(y,1.)
    for it in range(6):
        W=1/w; A=M.T@(M*W[:,None]); p=np.linalg.solve(A,M.T@(y*W)); m=M@p; w=np.maximum(m,0.5)
    cov=np.linalg.inv(A); chi=np.sum((y-m)**2/w)/max(len(y)-len(p),1)
    # background under peak (±1.25 FWHM ~ 3 sigma) for Currie limits
    B=[]
    for c,e in zip(chs,energies):
        s=sig_ch(e); mm=(x>=c-3*s)&(x<=c+3*s)
        B.append((p[0]+p[1]*(x[mm]-x.mean())).sum())
    return p[2:],np.sqrt(np.diag(cov))[2:],chi,np.array(B)
def analyse(key,lines=LINES,emin=20,emax=2800):
    cnt,lt,rt,_=load(key)
    L=sorted([l for l in lines if emin<l[0]<emax and l[1]!='annih'])
    # cluster lines within 5 channels
    groups=[]; cur=[L[0]]
    for l in L[1:]:
        if ch_of(l[0])-ch_of(cur[-1][0])<4: cur.append(l)
        else: groups.append(cur); cur=[l]
    groups.append(cur)
    out=[]
    for gr in groups:
        # merge exact-unresolvable (<0.6 keV) lines into one component
        en=[]; names=[]
        for l in gr:
            if en and abs(l[0]-en[-1])<0.7: names[-1]+= '+'+l[1]
            else: en.append(l[0]); names.append(l[1])
        A,dA,chi,B=fit_group(cnt,en)
        for e,n,a,da,b in zip(en,names,A,dA,B):
            LD=2.71+4.65*np.sqrt(b)  # Currie detection limit (counts)
            out.append(dict(E=e,nuc=n,A=a,dA=da,rate=a/lt,drate=da/lt,sig=a/da if da>0 else 0,chi=chi,LD=LD,lt=lt))
    return out
if __name__=='__main__':
    for k in ['TR','La']:
        print('=====',k)
        for r in analyse(k):
            flag='***' if r['A']>r['LD'] and r['sig']>3 else ''
            print(f"{r['E']:9.2f} {r['nuc']:22s} N={r['A']:8.1f}±{r['dA']:6.1f} ({r['sig']:5.1f}σ) LD={r['LD']:6.0f} rate={1e3*r['rate']:8.3f}±{1e3*r['drate']:6.3f} mcps chi2r={r['chi']:.2f} {flag}")
