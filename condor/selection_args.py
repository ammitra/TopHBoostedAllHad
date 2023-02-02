from glob import glob
import os

def GetAllFiles():
    return [f for f in glob('dijet_nano/*_snapshot.txt') if f != '']
def GetProcYearFromFile(filename):
    pieces = filename.split('/')[-1].split('.')[0].split('_')
    if '.txt' in filename:
        return pieces[0], pieces[1]
    else:
	return pieces[1], pieces[2]

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--HT', type=str, dest='HT',
                        action='store', default='0',
                         help='Value of HT to cut on')
    args = parser.parse_args()
    out = open('condor/selection_args_HT{}.txt'.format(args.HT),'w')
    files = GetAllFiles()
    for f in files:
	setname, era = GetProcYearFromFile(f)
   	if 'Data' not in setname and 'QCD' not in setname:
	    out.write('-s {} -y {} -v None --HT {}\n'.format(setname, era, args.HT))  # perform nominal variation first
	    JME = ['JES', 'JER', 'JMS', 'JMR']	# normal Jet corrections
	    if 'Tprime' in setname:
		JME.extend(['PNetTop', 'PNetXbb'])	# particleNet SF corrections (See THselection.py, need to be named PNet_up/down
	    for jme in JME:
	    	for v in ['up', 'down']:
		    out.write('-s {} -y {} -v {}_{} --HT {}\n'.format(setname, era, jme, v, args.HT))
    	else: 
	    out.write('-s {} -y {} -v None --HT {}\n'.format(setname, era, args.HT))
    out.close()
