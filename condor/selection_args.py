from glob import glob
import os

'''
out = open('condor/selection_args.txt','w')
for f in glob('dijet_nano/*.txt'):
    if os.path.getsize(f) == 0:
	print('File {} is empty, skipping...'.format(f))
	continue
    filename = f.split('/')[-1].split('.')[0]
    nfiles = len(open(f,'r').readlines())
    setname = filename.split('_')[0]
    year = filename.split('_')[1]


    njobs = int(nfiles/2)
    for i in range(1,njobs+1):
        out.write('-s %s -y %s -j %s -n %s \n'%(setname,year,i,njobs))
'''
def GetAllFiles():
    return [f for f in glob('dijet_nano/*_snapshot.txt') if f != '']
def GetProcYearFromFile(filename):
    pieces = filename.split('/')[-1].split('.')[0].split('_')
    if '.txt' in filename:
        return pieces[0], pieces[1]
    else:
	return pieces[1], pieces[2]

out = open('condor/selection_args.txt','w')
files = GetAllFiles()
for f in files:
    setname, era = GetProcYearFromFile(f)
    if 'Data' not in setname and 'QCD' not in setname:
	out.write('-s {} -y {} -v None \n'.format(setname, era))  # perform nominal variation first
	JME = ['JES', 'JER', 'JMS', 'JMR']	# normal Jet corrections
	if 'Tprime' in setname:
	    JME.extend(['PNetTop', 'PNetXbb'])	# particleNet SF corrections (See THselection.py, need to be named PNet_up/down
	for jme in JME:
	    for v in ['up', 'down']:
		out.write('-s {} -y {} -v {}_{} \n'.format(setname, era, jme, v))
    else: 
	out.write('-s {} -y {} -v None \n'.format(setname, era))

out.close()
