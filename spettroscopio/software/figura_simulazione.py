import json, numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
import sys; sys.path.insert(0,"/home/user/nav/spettroscopio/software")
from spettro import lambda_rgb
cal=json.load(open("cal_iph.json")); P=np.array(cal["polinomio"]); r0,r1=cal["righe"]
xs=np.arange(4032); lam=np.polyval(P,xs)
def xof(l): return int(xs[np.argmin(abs(lam-l))])
plt.rcParams.update({"font.size":9,"axes.spines.top":False,"axes.spines.right":False})
fig=plt.figure(figsize=(13,13.5),dpi=150,facecolor="white")
gs=fig.add_gridspec(4,3,height_ratios=[1.05,1.0,0.95,0.95],hspace=0.38,wspace=0.12)
nomi=[("cfl","Lampada fluorescente compatta"),("cielo","Cielo (luce diurna diffusa)"),("led","LED bianco")]
for i,(n,t) in enumerate(nomi):
    ax=fig.add_subplot(gs[0,i]); im=Image.open(f"iphone11_{n}.jpg")
    ax.imshow(im); ax.set_title(f"{t}\nfoto intera 4032×3024 (come la salva l'iPhone)",fontsize=9); ax.axis("off")
# 100% crops
def crop(n,l0,l1,ax,titolo,marks=()):
    im=np.asarray(Image.open(f"iphone11_{n}.jpg"))
    a,b=sorted([xof(l0),xof(l1)]); c0=(r0+r1)//2-110
    ax.imshow(im[c0:c0+220,a:b],interpolation="nearest",aspect="auto")
    ax.set_title(titolo,fontsize=9)
    ax.set_yticks([])
    tk=[l for l in marks]; ax.set_xticks([xof(l)-a for l in tk]); ax.set_xticklabels([("577/579" if l==578.0 else f"{l:g}") for l in tk],fontsize=7.5)
crop("cfl",660,560,fig.add_subplot(gs[1,0]),"CFL 100%: Eu 611 e Hg 577/579 separate.\nRighe curve = \"smile\"; righe scure = polvere",[611.6,578.0])
crop("cfl",560,400,fig.add_subplot(gs[1,1]),"CFL 100%: Hg 546, Tb 488, Hg 436, Hg 405\n(il viola è più sfocato: cromatica della lente)",[546.1,487.7,435.8,404.7])
crop("cielo",600,480,fig.add_subplot(gs[1,2]),"Cielo 100%: righe scure di Fraunhofer\n(Na D, Fe E, Mg b, Hβ)",[589.3,527.0,517.3,486.1])
# spectra
def spettro(n, ax, titolo, ann=()):
    d=np.genfromtxt(f"iphone11_{n}_spettro.csv",delimiter=",",names=True)
    x=d["lambda_nm"]; y=d["intensita"]/d["intensita"].max()
    for j in range(len(x)-1):
        ax.fill_between(x[j:j+2],0,y[j:j+2],color=lambda_rgb(x[j]),lw=0)
    ax.plot(x,y,color="#222",lw=.7); ax.set_xlim(380,720); ax.set_ylim(0,1.12)
    ax.set_title(titolo,fontsize=9.5,loc="left"); ax.set_xlabel("λ (nm)")
    for l,t in ann:
        k=np.argmin(abs(x-l)); ax.annotate(t,(l,y[k]),(l,min(1.08,y[k]+.16)),ha="center",fontsize=7.5,arrowprops=dict(arrowstyle="-",lw=.5))
ax=fig.add_subplot(gs[2,:2]); spettro("cfl",ax,f"Spettro estratto con spettro.py — CFL (calibrazione automatica: 7 righe, RMS {cal['rms_nm']:.2f} nm, FWHM ≈ {cal['fwhm_nm']:.1f} nm)",
  [(404.7,"Hg 404,7"),(435.8,"Hg 435,8"),(487.7,"Tb 488"),(546.1,"Hg 546,1"),(578,"Hg 577/579"),(611.6,"Eu 611,6")])
ax=fig.add_subplot(gs[2,2]); spettro("led",ax,"LED bianco: picco InGaN + fosforo YAG")
ax=fig.add_subplot(gs[3,:]); spettro("cielo",ax,"Cielo: righe di Fraunhofer (assorbimento dell'atmosfera solare e terrestre). Intensità come la vede il sensore (non corretta per la sua risposta): il calo oltre 650 nm è il filtro IR dell'iPhone.",
  [(431,"G (CH/Fe)"),(434.05,"Hγ"),(486.13,"Hβ"),(517.5,"Mg b"),(527.0,"Fe E"),(589.3,"Na D"),(656.28,"Hα"),(686.9,"O₂ B")])
fig.suptitle("Simulazione: iPhone 11 (camera principale 26 mm, f/1,8) + spettroscopio DVD, fenditura 50 µm, collimatore f 36 mm",fontsize=11.5,weight="bold",y=0.93)
fig.savefig("/home/user/nav/spettroscopio/render/simulazione_iphone11.png",bbox_inches="tight")
