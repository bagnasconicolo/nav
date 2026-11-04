import os
import sys,pickle; sys.path.insert(0,'.')
import numpy as np
res=pickle.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'res.pkl'),'rb'))
def get(k,E):
    for r in res[k]:
        if abs(r['E']-E)<0.3: return r['rate']*1e3, r['drate']*1e3
    raise KeyError(E)
def wfit(x,y,dy,deg):
    W=1/dy**2; V=np.vander(x,deg+1); A=V.T@(V*W[:,None]); p=np.linalg.solve(A,V.T@(y*W)); C=np.linalg.inv(A)
    chi=np.sum(W*(y-V@p)**2)/(len(x)-deg-1); return p,C,chi
def ev(p,C,x):
    v=np.vander(np.atleast_1d(x),len(p)); return v@p, np.sqrt(np.einsum('ij,jk,ik->i',v,C,v))
print("=== TRINITITE: relative efficiency from Eu-152 (rate/Igamma, mcps per %)")
eu=[(121.7817,28.53),(244.6974,7.55),(344.2785,26.59),(778.9045,12.93),(964.072,14.51),(1085.837,10.11),(1408.013,20.87)]
X=[];Y=[];DY=[]
for e,I in eu:
    r,d=get('TR',e)
    if abs(e-964.072)<0.1: r-=0.389; d=np.hypot(d,0.165)   # Ac-228 964.77 background (from La run)
    X.append(np.log(e));Y.append(np.log(r/I));DY.append(d/r)
    print(f"  {e:8.2f}  r={r:6.3f}±{d:5.3f} mcps  r/I={r/I:.4f}")
X,Y,DY=map(np.array,(X,Y,DY))
for deg in (1,2):
    p,C,chi=wfit(X,Y,DY,deg); print(f"  deg{deg}: chi2r={chi:.2f}")
p,C,chi=wfit(X,Y,DY,2); s=max(1,np.sqrt(chi))
def eps(e): v,d=ev(p,C,np.log(e)); return np.exp(v[0]), d[0]*s
for e,I in eu: print(f"   resid {e:7.1f}: {np.exp(np.log(get('TR',e)[0]/I)-np.log(eps(e)[0])):.3f}")
# activity relative to Eu-152 (A_x/A_Eu152): A ∝ r/(I*eps); Eu-152 normalisation: eps curve is r/I for Eu itself => A_Eu = 1 in these units
def ratio(E,I,r,dr):
    ef,def_=eps(E); A=r/I/ef; return A, A*np.hypot(dr/r,def_)
cs_r,cs_d=get('TR',661.657); cs_r-=4.013; cs_d=np.hypot(cs_d,0.254)  # subtract Cs-137 seen in La run (lab bkg)
A,dA=ratio(661.657,85.10,cs_r,cs_d); print(f"  A(Cs-137)/A(Eu-152) = {A:.1f} ± {dA:.1f}  (at measurement date)")
f_cs=2**(-81.27/30.08); f_eu=2**(-81.27/13.517); f_ba=2**(-81.27/10.551); f_154=2**(-81.27/8.601)
print(f"  decay factors since 16-Jul-1945: Cs137 {f_cs:.4f} Eu152 {f_eu:.4f} Ba133 {f_ba:.5f} Eu154 {f_154:.5f} Co60 {2**(-81.27/5.2714):.2e} Eu155 {2**(-81.27/4.753):.1e}")
print(f"  -> A(Cs-137)/A(Eu-152) at t0 = {A*f_eu/f_cs:.2f} ± {dA*f_eu/f_cs:.2f}")
ba_r,ba_d=get('TR',356.0129); A2,dA2=ratio(356.0129,62.05,ba_r,ba_d); print(f"  A(Ba-133)/A(Eu-152) = {A2:.3f} ± {dA2:.3f}; at t0 = {A2*f_eu/f_ba:.2f} ± {dA2*f_eu/f_ba:.2f}")
# Eu-154 upper limit via 1274.4 (LD)
for r in res['TR']:
    if abs(r['E']-1274.429)<0.1: LD=r['LD']/r['lt']*1e3
A3,_=ratio(1274.429,34.8,LD,1e-9); print(f"  Eu-154 1274 LD rate={LD:.3f} mcps -> A(Eu-154)/A(Eu-152) < {A3:.3f} (now); < {A3*f_eu/f_154:.2f} at t0")
for E,I,n in [(1173.228,99.85,'Co-60'),(1332.492,99.98,'Co-60')]:
    for r in res['TR']:
        if abs(r['E']-E)<0.1: L=r['LD']/r['lt']*1e3
    A4,_=ratio(E,I,L,1e-9); print(f"  {n} {E}: LD {L:.3f} mcps -> A/A(Eu152) < {A4:.4f}")
# Pu-239 / Am-241 using 51.6 vs 59.5
r51,d51=3.55,0.65; r59,d59=get('TR',59.5409)
base=(r51/0.0272)/(r59/35.92); db=base*np.hypot(d51/r51,d59/r59)
print(f"  [A(Pu239)/A(Am241)]*eps(51.6)/eps(59.5) = {base:.1f} ± {db:.1f}; for eps ratio 0.7-1.0 -> {base:.0f}-{base/0.7:.0f}")
r129,d129=get('TR',129.296); print(f"  Pu-239 129.3: {r129:.2f}±{d129:.2f}  ; consistency: expected 129.3 if eps(129)/eps(51.6)=1-2: ", f"{r51*0.00631/0.0272:.2f}-{2*r51*0.00631/0.0272:.2f} mcps")
print("\n=== La VIAL")
chain=[(235.96,12.9,'Th-227'),(256.23,7.0,'Th-227'),(329.85,2.9,'Th-227'),(269.459,13.9,'Ra-223'),(154.208,5.70,'Ra-223'),(323.871,3.99,'Ra-223'),(445.033,1.28,'Ra-223'),
       (401.81,6.6,'Rn-219'),(404.853,3.78,'Pb-211'),(427.088,1.76,'Pb-211'),(831.96,3.5,'Pb-211'),(351.06,13.0,'Bi-211')]
pts=[]
for E,I,n in chain:
    r,d=get('La',E)
    if n=='Bi-211':
        # Bi-211 351.06 and Pb-214 351.93 unresolved: take total and subtract Pb-214 351.9 estimated from Pb-214 295.2 (ratio from TR run)
        tot=get('La',351.06)[0]+get('La',351.932)[0]; dt=np.hypot(get('La',351.06)[1],get('La',351.932)[1])
        k=get('TR',351.932)[0]/get('TR',295.224)[0]
        pb=get('La',295.224)[0]*1.70  # Igamma ratio 35.6/18.4 x eff ratio ~0.88
        r=tot-pb; d=np.hypot(dt,0.3*pb)
    pts.append((E,I,n,r,d)); print(f"  {n:7s} {E:7.2f} r={r:6.2f}±{d:4.2f}  r/I={r/I:.3f}±{d/I:.3f}")
X=np.log([p_[0] for p_ in pts]); Y=np.log([p_[3]/p_[1] for p_ in pts]); DY=np.array([p_[4]/p_[3] for p_ in pts])
for deg in (1,2):
    pc,Cc,chic=wfit(X,Y,DY,deg); print(f"  chain eff fit deg{deg} chi2r={chic:.2f}", np.round(pc,3))
pc,Cc,chic=wfit(X,Y,DY,1)
for E,I,n,r,d in pts: print(f"   resid {n} {E:.1f}: {(r/I)/np.exp(ev(pc,Cc,np.log(E))[0][0]):.3f}")
# La-138
r789,d789=get('La',788.742); r1436,d1436=get('La',1435.795)
chain_at_789=np.exp(ev(pc,Cc,np.log(788.742))[0][0]); dchain=ev(pc,Cc,np.log(788.742))[1][0]*max(1,np.sqrt(chic))
for I789 in (34.5,34.8):
    la=r789/I789; R=chain_at_789/la; dR=R*np.hypot(dchain,d789/r789)
    print(f"  I(789)={I789}%:  A(Ac-227 chain member)/A(La-138) = {R:.3f} ± {dR:.3f}")
# direct 832 vs 789 only
r832,d832=get('La',831.96); epsr=(831.96/788.742)**pc[0]
R2=(r832/3.5/epsr)/(r789/34.5); print(f"  direct 832/789: {R2:.2f} ± {R2*np.hypot(d832/r832,d789/r789):.2f} (eps slope {pc[0]:.2f})")
print(f"  138La 1436/789 check: eps(1436)/eps(789) = {(r1436/65.5)/(r789/34.5):.3f} (power-law from chain slope predicts {(1435.8/788.7)**pc[0]:.3f})")
# specific activity of 138La in natural La
NA=6.02214e23; M=138.905; ab=0.0008881; T=1.03e11*365.25*86400
SA=NA/M*ab*np.log(2)/T; print(f"  138La specific activity in natural La: {SA:.3f} Bq/g La")
lamAc=np.log(2)/(21.772*365.25*86400)
for Rr in (R,):
    aAc=Rr*SA; atoms=aAc/lamAc; print(f"  => A(Ac-227) ≈ {aAc:.2f} ± {aAc*dR/R:.2f} Bq per g La ; Ac/La atom ratio ≈ {atoms/(NA/M):.2e}")
