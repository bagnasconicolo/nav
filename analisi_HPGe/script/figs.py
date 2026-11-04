import os
import sys; sys.path.insert(0,'.')
from fit2 import *
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':10})
cT,lT,_,_=load('TR'); cL,lL,_,_=load('La'); ch=np.arange(2048); e=np.polyval(cE,ch)
C1,C2='#1f5fa8','#d1661f'
def ann(ax,items,c,ymax):
    for E,t in items:
        ax.axvline(E,color=c,lw=.5,ls=':',alpha=.7)
        ax.text(E,ymax,t,rotation=90,va='top',ha='right',fontsize=7.5,color=c)
# Fig1 overview
fig,ax=plt.subplots(2,1,figsize=(13,8.5),sharex=True)
for a,c,lt,col,name,items in [(ax[0],cT,lT,C1,'Trinitite (LT = %.0f s)'%lT,[(59.54,'Am-241'),(121.78,'Eu-152'),(344.28,'Eu-152'),(661.66,'Cs-137'),(778.9,'Eu-152'),(964.1,'Eu-152'),(1408.0,'Eu-152'),(1460.8,'K-40 (fondo)'),(2614.5,'Tl-208 (fondo)'),(1764.5,'Bi-214 (fondo)'),(511,'annich.')]),
                              (ax[1],cL,lL,C2,'Fiala di La (LT = %.0f s)'%lL,[(235.96,'Th-227'),(269.5,'Ra-223/Rn-219'),(351.06,'Bi-211'),(401.8,'Rn-219'),(788.74,'La-138'),(831.96,'Pb-211'),(1435.8,'La-138'),(1460.8,'K-40 (fondo)'),(2614.5,'Tl-208 (fondo)'),(84,'raggi X'),(154.2,'Ra-223')])]:
    a.step(e,c/lt,where='mid',color=col,lw=.7); a.set_yscale('log'); a.set_ylim(5e-6,1); a.set_title(name,loc='left'); a.set_ylabel('conteggi/s/canale'); a.grid(alpha=.25)
    ann(a,items,'k',0.9)
ax[1].set_xlabel('Energia (keV)'); ax[1].set_xlim(15,2800)
plt.tight_layout(); plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','figure','fig1_spettri.png'),dpi=130); plt.close()
# zoom helper
def zoom(ax,lo,hi,items,log=False,title=''):
    m=(e>=lo)&(e<=hi)
    ax.step(e[m],cT[m]/lT*1e3,where='mid',color=C1,lw=.9,label='Trinitite')
    ax.step(e[m],cL[m]/lL*1e3,where='mid',color=C2,lw=.9,label='Fiala La')
    if log: ax.set_yscale('log')
    ymax=ax.get_ylim()[1]; ann(ax,items,'k',ymax*0.98 if not log else ymax*0.9)
    ax.set_xlim(lo,hi); ax.set_title(title,loc='left',fontsize=9.5); ax.set_ylabel('mcps/canale'); ax.grid(alpha=.25)
fig,ax=plt.subplots(3,2,figsize=(13,11))
zoom(ax[0,0],40,140,[(51.62,'Pu-239 51.6'),(59.54,'Am-241 59.5'),(74.97,'Pb Kα'),(84.94,'Pb Kβ'),(92.6,'Th-234'),(121.78,'Eu-152 121.8'),(129.3,'Pu-239 129.3')],log=True,title='a) Trinitite 40–140 keV')
zoom(ax[0,1],330,370,[(338.3,'Ac-228'),(344.28,'Eu-152'),(351.93,'Pb-214'),(356.01,'Ba-133')],title='b) Trinitite 330–370 keV')
zoom(ax[1,0],640,680,[(661.66,'Cs-137')],log=True,title='c) Cs-137')
zoom(ax[1,1],760,800,[(768.4,'Bi-214'),(778.9,'Eu-152'),(788.74,'La-138')],title='d) 760–800 keV')
zoom(ax[2,0],1380,1480,[(1408.01,'Eu-152'),(1435.8,'La-138'),(1460.82,'K-40')],title='e) 1380–1480 keV')
zoom(ax[2,1],1160,1345,[(1173.2,'Co-60 (assente)'),(1238.1,'Bi-214'),(1274.4,'Eu-154 (assente)'),(1332.5,'Co-60 (assente)')],title='f) Co-60 / Eu-154 (non rivelati)')
for a in ax[2]: a.set_xlabel('Energia (keV)')
ax[0,0].legend(loc='upper right',fontsize=8)
plt.tight_layout(); plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','figure','fig2_zoom_trinitite.png'),dpi=130); plt.close()
fig,ax=plt.subplots(2,1,figsize=(13,8))
zoom(ax[0],140,460,[(144.2,'Ra-223'),(154.2,'Ra-223'),(185.7,'U-235/Ra-226'),(210.6,'Th-227'),(235.96,'Th-227'),(256.23,'Th-227'),(269.46,'Ra-223'),(271.23,'Rn-219'),(286.1,'Th-227'),(300,'Th-227'),(323.87,'Ra-223'),(329.85,'Th-227'),(338.28,'Ra-223'),(351.06,'Bi-211'),(401.81,'Rn-219'),(404.85,'Pb-211'),(427.09,'Pb-211'),(445.03,'Ra-223')],title='a) Fiala La 140–460 keV: catena del 227Ac')
zoom(ax[1],760,860,[(768.4,'Bi-214'),(788.74,'La-138'),(831.96,'Pb-211')],title='b) Fiala La 760–860 keV')
ax[1].set_xlabel('Energia (keV)'); ax[0].legend(fontsize=8,loc='center right')
plt.tight_layout(); plt.savefig(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','figure','fig3_zoom_lantanio.png'),dpi=130); plt.close()
