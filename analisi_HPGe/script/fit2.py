import sys; sys.path.insert(0,'.')
from libfit import load,ch_of,sig_ch,g,cE,np
def fit_group2(cnt,energies,half=6,shifts=np.arange(-0.6,0.61,0.03),wsc=np.arange(0.8,1.41,0.05)):
    chs=np.array([ch_of(e) for e in energies])
    lo=int(np.floor(chs.min()-half)); hi=int(np.ceil(chs.max()+half))+1
    x=np.arange(lo,hi).astype(float); y=cnt[lo:hi]
    best=None
    for sh in shifts:
        for ws in wsc:
            M=np.array([np.ones_like(x),x-x.mean()]+[g(x,c+sh,ws*sig_ch(e)) for c,e in zip(chs,energies)]).T
            w=np.maximum(y,1.)
            for it in range(4):
                A=M.T@(M/w[:,None]); p=np.linalg.solve(A,M.T@(y/w)); m=M@p; w=np.maximum(m,0.5)
            chi=np.sum((y-m)**2/w)
            if best is None or chi<best[0]: best=(chi,sh,ws,p,np.linalg.inv(A),m)
    chi,sh,ws,p,cov,m=best
    B=[]
    for c,e in zip(chs,energies):
        s=ws*sig_ch(e); mm=(x>=c+sh-3*s)&(x<=c+sh+3*s); B.append(max((p[0]+p[1]*(x[mm]-x.mean())).sum(),0))
    return dict(A=p[2:],dA=np.sqrt(np.diag(cov))[2:],chi=chi/max(len(y)-len(p)-2,1),sh=sh*cE[1],ws=ws,B=np.array(B),x=x,y=y,m=m)
def analyse2(key,lines,gap=4.5,verbose=True):
    cnt,lt,rt,_=load(key)
    L=sorted(lines)
    groups=[]; cur=[L[0]]
    for l in L[1:]:
        if ch_of(l[0])-ch_of(cur[-1][0])<gap: cur.append(l)
        else: groups.append(cur); cur=[l]
    groups.append(cur); out=[]
    for gr in groups:
        en=[]; names=[]; I=[]
        for l in gr:
            if en and abs(l[0]-en[-1])<0.7: names[-1]+='+'+l[1]
            else: en.append(l[0]); names.append(l[1])
        r=fit_group2(cnt,en)
        for i,(e,n) in enumerate(zip(en,names)):
            a,da,b=r['A'][i],r['dA'][i],r['B'][i]
            LD=2.71+4.65*np.sqrt(b)
            d=dict(E=e,nuc=n,A=a,dA=da,rate=a/lt,drate=da/lt,LD=LD,LC=2.33*np.sqrt(b),chi=r['chi'],sh=r['sh'],ws=r['ws'],lt=lt)
            out.append(d)
            if verbose:
                flag='DET' if a>d['LC'] and a>3*da else ('(?)' if a>d['LC'] else '')
                print(f"{e:9.2f} {n:24s} N={a:8.1f}±{da:6.1f} LC={d['LC']:5.0f} LD={LD:5.0f} r={1e3*a/lt:8.3f}±{1e3*da/lt:6.3f} mcps chi2r={r['chi']:5.2f} dE={r['sh']:+.2f} w={r['ws']:.2f} {flag}")
    return out
