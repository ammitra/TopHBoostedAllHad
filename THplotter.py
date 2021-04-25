from argparse import Namespace
from glob import glob
from THselection import main
from TIMBER.Tools.Common import DictStructureCopy
import multiprocessing

def GetAllFiles():
    return glob('dijet_nano/*_snapshot.txt')

def GetProcYear(filename):
    pieces = filename.split('/')[-1].split('.')[0].split('_')
    return pieces[0], pieces[1]

def GetFileDict(all_files):
    by_year = {
        16: {'bkg':[],'sig':[],'data':None},
        17: {'bkg':[],'sig':[],'data':None},
        18: {'bkg':[],'sig':[],'data':None}
    }
    for f in all_files:
        proc, year = GetProcYear(f)
        if 'Tprime' in proc:
            by_year[year]['sig'].append(f)
        elif proc == 'Data':
            by_year[year]['data'] = f
        else:
            by_year[year]['bkg'].append(f)
    return by_year

def multicore():
    files = GetAllFiles()
    args = Namespace()
    pool = multiprocessing.Pool(processes=4)
    process_args = []
    for f in files:
        args.proc, args.year = GetProcYear(f)
        args.threads = 4
        process_args.append(args)
        if 'Data' not in args.proc and 'QCD' not in args.proc:
            for jme in ['JES','JER','JMS','JMR']:
                for v in ['up','down']:
                    process_args.append(args + ' -v %s_%s'%(jme,v))
    pool.map(main,process_args)

def plot():
    hists = DictStructureCopy(GetAllFiles())

