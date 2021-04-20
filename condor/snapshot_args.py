import glob

out = open('condor/snapshot_args.txt','w')
for f in glob.glob('raw_nano/*.txt'):
    filename = f.split('/')[-1].split('.')[0]
    setname = filename.split('_')[0]
    year = filename.split('_')[1]
    if 'Tprime' in setname:
        out.write('-s %s -y %s\n'%(setname,year))
    else:
        njobs = 10
        for i in range(1,njobs+1):
            out.write('-s %s -y %s -j %s -n %s \n'%(setname,year,i,njobs))

out.close()