from glob import glob
import subprocess, os

from TIMBER.Tools.Common import ExecuteCmd
redirector = 'root://cmseos.fnal.gov/'
eos_path = '/store/user/%s/topHBoostedAllHad/snapshots/'%os.getenv('USER')

files = subprocess.check_output('eos root://cmseos.fnal.gov ls %s'%(eos_path), shell=True)
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
    ExecuteCmd('cat dijet_nano/Data*_{0}_snapshot.txt > dijet_nano/Data_{0}_snapshot.txt'.format(y))
    for s in subdatafiles:
        ExecuteCmd('rm %s'%s)