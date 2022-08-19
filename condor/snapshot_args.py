import glob,os

out = open('condor/snapshot_args.txt','w')

for f in glob.glob('raw_nano/*.txt'):
    if os.path.getsize(f) == 0:
        print ('File %s is empty... Skipping.'%(f))
        continue

    filename = f.split('/')[-1].split('.')[0]
    nfiles = len(open(f,'r').readlines())
    setname = filename.split('_')[0]
    year = filename.split('_')[1]

    njobs = int(nfiles/2)
    if njobs == 0:	# this occurs when nfiles = 1
	njobs += 1
    for i in range(1,njobs+1):
	out.write('-s %s -y %s -j %s -n %s \n'%(setname,year,i,njobs))

out.close()
