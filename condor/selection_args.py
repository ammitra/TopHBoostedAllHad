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
    out = open('condor/selection_args.txt','w')
    files = GetAllFiles()
    for f in files:
        if 'snapshot' not in f: continue
        if 'Muon' in f: continue
        setname, era = GetProcYearFromFile(f)
        if 'Data' not in setname and 'QCD' not in setname:
            out.write('-s {} -y {} -v None\n'.format(setname, era))  # perform nominal variation first
            JME = ['JES', 'JER', 'JMS', 'JMR']	# normal Jet corrections
            for jme in JME:
                for v in ['up', 'down']:
                    out.write('-s {} -y {} -v {}_{}\n'.format(setname, era, jme, v))
        else: 
            out.write('-s {} -y {} -v None\n'.format(setname, era))

    out.close()
