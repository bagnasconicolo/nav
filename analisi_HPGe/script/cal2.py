import numpy as np
# (E_ref, centroid) from well-defined peaks
pts=[(59.5409,42.634),(661.657,477.446),(1460.82,1053.827),(2614.511,1885.662),
     (351.06,253.442),(788.742,569.049),(1435.795,1035.715),(1460.82,1053.71),(2614.511,1885.569)]
Er=np.array([a for a,b in pts]); ch=np.array([b for a,b in pts])
c=np.polyfit(ch,Er,2); print('E(ch) coeffs (c2,c1,c0):',c); print('resid keV',np.round(Er-np.polyval(c,ch),3))
c1=np.polyfit(ch,Er,1); print('linear',c1, np.round(Er-np.polyval(c1,ch),3))
# FWHM model from reliable fits (keV)
F=[(351.06,1.44),(661.657,1.44),(788.742,1.57),(1435.795,2.05),(1460.82,1.97),(1460.82,2.12),(2614.511,2.42),(2614.511,2.74),(1764.49,1.88),(1764.49,2.26)]
e=np.array([a for a,b in F]); f=np.array([b for a,b in F])
ab=np.polyfit(e,f**2,1); print('FWHM^2 = %.4f + %.6f E'%(ab[1],ab[0])); print([ (x,round(np.sqrt(np.polyval(ab,x)),2)) for x in [60,122,344,662,1000,1408,2614]])
import os; np.save(os.path.join(os.path.dirname(os.path.abspath(__file__)),'cal.npy'),np.r_[c,ab])
