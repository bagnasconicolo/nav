import numpy as np, re
import os
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","dati")+"/"
FILES={'La':D+'Lantan_28 ottobre 2026.Spe','TR':D+'Sabbia_vetrificata_21 ottobre 2026.Spe'}
def load(key):
    L=open(FILES[key]).read().splitlines()
    i=L.index('$MEAS_TIM:'); lt,rt=map(float,L[i+1].split())
    i=L.index('$DATA:'); a,b=map(int,L[i+1].split())
    c=np.array([float(x) for x in L[i+2:i+3+b-a]])
    i=L.index('$MCA_CAL:'); p=[float(x) for x in L[i+2].split()[:3]]
    return c,lt,rt,p
def E(ch,p): return p[0]+p[1]*ch+p[2]*ch**2
def snip(y,m=24):
    v=np.log(np.log(np.sqrt(y+1)+1)+1)
    for k in range(1,m+1):
        a=v.copy(); a[k:-k]=np.minimum(v[k:-k],(v[:-2*k]+v[2*k:])/2); v=a
    return (np.exp(np.exp(v)-1)-1)**2-1
