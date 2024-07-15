'''
script to test and debug RDF JITing
'''
import ROOT
from TIMBER.Analyzer import *

verbosity = ROOT.Experimental.RLogScopedVerbosity(ROOT.Detail.RDF.RDFLogChannel(), ROOT.Experimental.ELogLevel.kDebug+10)

a = analyzer('root://cmsxrootd.fnal.gov//store/mc/RunIISummer20UL18NanoAODv9/TprimeBToTH_THad_Hbb_LH_MT1800_MH125_TuneCP5_13TeV-madgraph-pythia8/NANOAODSIM/106X_upgrade2018_realistic_v16_L1v1-v1/250000/A5EF5C55-6619-DF47-A72F-DA5284B3C39B.root')

ROOT.gInterpreter.Declare("""
ROOT::VecOps::RVec<int> make_vect() {
    return {0,1};
}
""")

a.Cut('jetCut','nFatJet >= 2')
a.Cut('jetId', 'Jet_jetId[0] > 1 && Jet_jetId[1] > 1')
a.Cut('pT', 'FatJet_pt[0] > 350 && FatJet_pt[1] > 350')
a.Define('DijetIdxs','make_vect()')
a.SubCollection('Dijet','FatJet','DijetIdxs',useTake=True)

