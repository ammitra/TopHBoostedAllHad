import glob, os

with open('../condor/highMassTprime_pileup_args.txt','w') as f:
    for filename in glob.glob('./*.txt'):
        if os.path.getsize(filename) == 0:
            print ('File %s is empty... Skipping.'%(filename))
            continue
        pieces = filename.split('/')[-1].split('.')[0].split('_')
        setname, year = pieces[0], pieces[1]
        f.write('-s %s -y %s\n'%(setname,year))
