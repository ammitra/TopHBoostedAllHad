'''
Script to run over all data and generate snapshots which specify if the data came from run 2017B or not.
This information is used to determine the amount of data which remains from 2017B after preselection to 
help decide whether or not dropping 2017B is justified.
'''

import ROOT, time
ROOT.gROOT.SetBatch(True)
# ROOT.ROOT.EnableImplicitMT(2)
from TIMBER.Tools.Common import CompileCpp
from argparse import ArgumentParser
from THClass import THClass
from array import array

parser = ArgumentParser()
parser.add_argument('-s', type=str, dest='setname',
                    action='store', required=True,
                    help='Setname to process.')
parser.add_argument('-y', type=str, dest='era',
                    action='store', required=True,
                    help='Year of set (16, 17, 18).')
parser.add_argument('-j', type=int, dest='ijob',
                    action='store', default=1,
                    help='Job number')
parser.add_argument('-n', type=int, dest='njobs',
                    action='store', default=1,
                    help='Number of jobs')
args = parser.parse_args()

start = time.time()

CompileCpp('THmodules.cc')
selection = THClass('raw_nano/%s_%s.txt'%(args.setname,args.era),args.era,args.ijob,args.njobs)
selection.ApplyKinematicsSnap()
selection.ApplyStandardCorrections(snapshot=True)
if ((args.setname=='DataB') and (args.era=='17')):
    out = selection.a.Define("is2017B", "1")
else:
    out = selection.a.Define("is2017B", "0")
selection.Snapshot(out,colNames=["is2017B"])

print ('%s sec'%(time.time()-start))
