import os,pickle,csv
H=os.path.dirname(os.path.abspath(__file__))
res=pickle.load(open(os.path.join(H,'res.pkl'),'rb'))
for k,name in [('TR','trinitite'),('La','fiala_lantanio')]:
    with open(os.path.join(H,'..',f'picchi_{name}.csv'),'w',newline='') as f:
        w=csv.writer(f); w.writerow(['E_keV','nuclide','area_netta','sigma_area','rate_mcps','sigma_rate_mcps','L_C','L_D','esito'])
        for r in res[k]:
            esito='rivelato' if (r['A']>r['LC'] and r['A']>3*r['dA']) else ('incerto' if r['A']>r['LC'] else 'non rivelato')
            w.writerow([f"{r['E']:.2f}",r['nuc'],f"{r['A']:.1f}",f"{r['dA']:.1f}",f"{1e3*r['rate']:.3f}",f"{1e3*r['drate']:.3f}",f"{r['LC']:.0f}",f"{r['LD']:.0f}",esito])
