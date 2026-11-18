import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
a=np.arcsin(550/740); u=np.array([-np.sin(a),np.cos(a)]); n=np.array([np.cos(a),np.sin(a)])
G=np.array([0,11.6]); P=lambda s,o=0: G+u*s+n*o
fig,ax=plt.subplots(figsize=(10,8),dpi=160); grey="#d9d9d6"; blk="#1c1c1e"
ax.add_patch(Rectangle((-70,-8.3),95,8.3,color="#2b2b2e")); ax.text(-55,-5,"telefono",color="w",fontsize=10)
ax.add_patch(Rectangle((-3,-1.4),6,1.4,color="#777"))
for x0 in [-19,15.15]: ax.add_patch(Rectangle((x0,0),3.85,6.4,color="#bdbdb8"))
ax.add_patch(Polygon([(-17,6.4),(-15,6.4),(-15,0.4),(15,0.4),(15,6.4),(17,6.4),tuple(P(14,14.5)),tuple(P(14,-14.5))],color=grey))
ax.add_patch(Polygon([(-13.2,1.6),(13.2,1.6),(7,9.9),(-7,9.9)],color=blk)); ax.add_patch(Rectangle((-4.5,0.4),9,1.2,color=blk))
ax.add_patch(Polygon([tuple(P(0,-6)),tuple(P(0,6)),tuple(P(20,6)),tuple(P(20,-6))],color=blk))
ax.add_patch(Rectangle((-8.7,9.9),17.4,2.0,color="#4a78d0")); ax.add_patch(Rectangle((-6,9.9),12,1.4,color=blk))
ax.add_patch(Rectangle((-7.5,11.3),15,0.6,color="#f2b630",zorder=5))
L=55.4
ax.add_patch(Polygon([tuple(P(14,14.5)),tuple(P(L,14.5)),tuple(P(L,-14.5)),tuple(P(14,-14.5))],color=grey))
ax.add_patch(Polygon([tuple(P(14,10)),tuple(P(L-6,10)),tuple(P(L-3.5,1.3)),tuple(P(L-3.5,-1.3)),tuple(P(L-6,-10)),tuple(P(14,-10))],color=blk))
s_flat=14+7.76; R=17.06; rr=np.linspace(-12.5,12.5,60); sag=R-np.sqrt(R**2-rr**2)
dome=[tuple(P(s_flat-1.05-(5.45-sg),r)) for r,sg in zip(rr,sag)]
ax.add_patch(Polygon([tuple(P(s_flat,12.5))]+dome[::-1]+[tuple(P(s_flat,-12.5))],color="#9cc8f0",zorder=4))
for sg in [1,-1]: ax.add_patch(Polygon([tuple(P(L-2,sg*0.15)),tuple(P(L-2,sg*9)),tuple(P(L-1.6,sg*9)),tuple(P(L-1.6,sg*0.15))],color="#888",zorder=6))
sl=P(L-2)
for o in [-4,0,4]:
    A=P(s_flat,o); k=-(n*o)[1]/u[1]; B=G+n*o+u*k
    ax.plot(*zip(sl,A),color="#fff176",lw=1,zorder=7); ax.plot(*zip(A,B),color="#fff176",lw=1,zorder=7)
for lam,col in [(435.8,"#3d5afe"),(546.1,"#43a047"),(611.6,"#e53935")]:
    b=np.arcsin(lam/740-np.sin(a)); d=np.array([np.sin(b),-np.cos(b)]); ax.plot(*zip(G,G+d*12.5),color=col,lw=2,zorder=8)
d0=-u; ax.plot(*zip(G,G+d0*13),color="#bbb",lw=1.2,ls="--",zorder=8)
def lab(t,xy,xyt): ax.annotate(t,xy,xyt,fontsize=9.5,arrowprops=dict(arrowstyle="-",lw=.6,color="#555"),zorder=10)
lab("PEZZO DI DVD (15×15 mm): la luce lo ATTRAVERSA\nè nella cassetta blu, parallelo al telefono,\n~11 mm sopra l'obiettivo",(5,11.6),(14,22))
lab("cassetta estraibile (blu)\nsi infila di lato nella base",(8,10.5),(24,5))
lab("camera oscura",(-9,4),(-52,6))
lab("ordine zero (luce non deviata)\n→ finisce contro il nero",tuple(G+d0*11),(22,-14))
lab("lente piano-convessa f 36\n(lato piatto verso la fenditura)",tuple(P(s_flat-3,-8)),(-66,26))
lab("fenditura: 2 lame a 0,05 mm",tuple(P(L-2,-5)),(-66,52))
lab("raggi paralleli",tuple(P(8,0)),(-66,38))
lab("blu / verde / rosso\nverso la fotocamera",(-1.2,4),(-60,15))
lab("obiettivo della fotocamera",(0,-0.7),(-38,-16))
ax.text(-66,61,"Sezione dello spettroscopio (scala reale, mm)",fontsize=11,weight="bold")
ax.set_aspect("equal"); ax.set_xlim(-68,48); ax.set_ylim(-22,64); ax.axis("off")
fig.tight_layout(); fig.savefig("render/schema_ottico.png")
