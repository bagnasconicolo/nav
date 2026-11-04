from lib import LINES
BKG=['U-235','Ra-226','U-235+Ra-226','Th-234','Pa-234m','Pb-214','Bi-214','Ac-228','Pb-212','Bi-212','Tl-208','K-40','Tl-208 DE','Tl-208 SE','Pb-210']
XR=[(72.80,'Pb Ka2',0),(74.97,'Pb Ka1',0),(84.94,'Pb Kb1',0),(87.3,'Pb Kb2',0)]
TRN=['Am-241','Cs-137','Eu-152','Eu-154','Eu-155','Ba-133','Co-60','Pu-239']
LAN=['La-138','Th-227','Ra-223','Rn-219','Pb-211','Bi-211','Tl-207']
def pick(nucs,emin=30,extra=[]):
    out=[l for l in LINES if l[1] in nucs and l[0]>emin]+extra
    out.append((511.0,'annih(+Tl-208 510.8)',0))
    return [l for l in out if not (l[1]=='Tl-208' and abs(l[0]-510.77)<1)]
TR_LIB=pick(TRN+BKG,extra=XR)
LA_LIB=pick(LAN+BKG,extra=XR+[(210.62,'Th-227',1.25),(31.98,'Ba Ka',0),(36.4,'Ba Kb',0),(81.1,'Rn Ka2/Bi Kb',0),(83.8,'Rn Ka1',0),(88.5,'Ra Ka1',0),(85.4,'Ra Ka2',0),(93.4,'Th Ka1',0),(89.95,'Th Ka2',0),(79.69,'Th-227/Fr-223',2.0),(113.17,'Th-227',0.0)])
