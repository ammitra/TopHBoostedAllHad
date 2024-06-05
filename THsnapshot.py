import ROOT, time
ROOT.gROOT.SetBatch(True)
#ROOT.ROOT.EnableImplicitMT(2)
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
selection.LeptonVeto()
out = selection.ApplyStandardCorrections(snapshot=True)

# execute all of the GetValue() calls to access the cutflow information
for cut in ['NPROC','NFLAGS','NJETS','NJETID','NPT','NKIN','PreLeptonVeto','NTightMu','NTightEl','NGoodMu','NGoodEl','PostLeptonVeto']:
    #getattr(selection,cut).GetValue()
    print('Doing cutflow for: %s'%cut)
    selection.AddCutflowColumn(getattr(selection,cut).GetValue(), cut)

selection.Snapshot(out)

print ('%s sec'%(time.time()-start))
