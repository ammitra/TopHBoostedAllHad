from glob import glob
import subprocess, os

from TIMBER.Tools.Common import ExecuteCmd
redirector = 'root://cmseos.fnal.gov/'
eos_path = '/store/user/ammitra/topHBoostedAllHad/snapshot/'

files = subprocess.check_output('eos root://cmseos.fnal.gov ls %s'%(eos_path), shell=True, text=True)
org_files = {}
for f in files.split('\n'):
    if f == '': continue
    info = f.split('.')[0].split('_')
    setname = info[1]
    year = info[2]
    file_path = redirector+eos_path+f

    if year not in org_files.keys():
        org_files[year] = {}
    if setname not in org_files[year].keys():
        org_files[year][setname] = []

    org_files[year][setname].append(file_path)

 
for y in org_files.keys():
    for s in org_files[y].keys():
        out = open('dijet_nano/%s_%s_snapshot.txt'%(s,y),'w')
        for f in org_files[y][s]:
            out.write(f+'\n')
        out.close()

    # consolidate data files
    subdatafiles = glob('dijet_nano/Data*_%s_snapshot.txt'%y)
    ExecuteCmd('rm dijet_nano/Data_{0}_snapshot.txt'.format(y))
    ExecuteCmd('cat dijet_nano/Data*_{0}_snapshot.txt > dijet_nano/Data_{0}_snapshot.txt'.format(y))

    # consolidate single muon data files
    singlemuonfiles = glob('dijet_nano/SingleMuonData*_{}_snapshot.txt'.format(y))
    ExecuteCmd('rm dijet_nano/SingleMuonData_{}_snapshot.txt'.format(y))
    ExecuteCmd('cat dijet_nano/SingleMuonData*_{0}_snapshot.txt > dijet_nano/SingleMuonData_{0}_snapshot.txt'.format(y))


# now, since 2017B has fewer triggers (poor efficiency) and will be omitted, we need to omit it from the respective data files
# rename concatenated 2017 data (2017B inclusive) to new file 
ExecuteCmd('mv dijet_nano/SingleMuonData_17_snapshot.txt dijet_nano/SingleMuonDataWithB_17_snapshot.txt')
# remove 17B data from concatenated files 
ExecuteCmd('cat dijet_nano/SingleMuonDataWithB_17_snapshot.txt | grep -v DataB > dijet_nano/SingleMuonData_17_snapshot.txt')

# do the same thing for JetHT data
ExecuteCmd('mv dijet_nano/Data_17_snapshot.txt dijet_nano/DataWithB_17_snapshot.txt')
ExecuteCmd('cat dijet_nano/DataWithB_17_snapshot.txt | grep -v DataB > dijet_nano/Data_17_snapshot.txt')

