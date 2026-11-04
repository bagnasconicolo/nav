import os
import sys; sys.path.insert(0,'.')
from fit2 import *; from libs import *; import pickle
res={}
for k,lib in [('TR',TR_LIB),('La',LA_LIB)]:
    print('=====',k); res[k]=analyse2(k,lib)
pickle.dump(res,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'res.pkl'),'wb'))
