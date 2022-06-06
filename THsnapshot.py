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
selection = THClass('raw_nano/%s_%s.txt'%(args.setname,args.era),int(args.era),args.ijob,args.njobs)
selection.ApplyKinematicsSnap()
out = selection.ApplyStandardCorrections(snapshot=True)
selection.Snapshot(out)

'''
# DEPRECATED
# now extract and save the cutflow information
print('Extracting and saving cutflow information')
f = ROOT.TFile.Open('THsnapshot_%s_%s_%sof%s.root'%(args.setname,args.era,args.ijob,args.njobs),'UPDATE')
cutFlowTree = ROOT.TTree('cutFlow_snapshot','friend tree containing cutflow from snapshot phase')

nProc = array('f', [selection.nProc])
nJets = array('f', [selection.nJets])
npT = array('f', [selection.npT])
nKin = array('f', [selection.nKin])

print('nProc:  {}'.format(nProc))
print('nJets:  {}'.format(nJets))
print('npT:    {}'.format(npT))
print('nKin:   {}'.format(nKin))

cutFlowTree.Branch('nProc', nProc, 'nProc/F')
cutFlowTree.Branch('nJets', nJets, 'nJets/F')
cutFlowTree.Branch('npT', npT, 'npT/F')
cutFlowTree.Branch('nKin', nKin, 'nKin/F')

print('Filling and writing cutflow TTree...')
cutFlowTree.Fill()
cutFlowTree.Write("", ROOT.TObject.kOverwrite);

print('Adding cutflow TTree as Friend...')
events = f.Get('Events')
events.AddFriend(cutFlowTree)
f.Close()
'''
print ('%s sec'%(time.time()-start))
