import ROOT
from TIMBER.Analyzer import analyzer
from TIMBER.Tools.Common import ExecuteCmd, CompileCpp

proc = 'ttbar'

#a = analyzer('TEST_ddt_12800-125_18.root')
a = analyzer('dijet_nano/{}_18_snapshot.txt'.format(proc))
ROOT.gInterpreter.Declare('TFile* f = TFile::Open("DDTMaps_Run2018UL.root","READ");')
CompileCpp('checkDDT.cc')

#a.Define('ddt_discr0','DDT_discr(f, Dijet_pt[0], Dijet_msoftdrop[0])')
#a.Define('ddt_discr1','DDT_discr(f, Dijet_pt[1], Dijet_msoftdrop[1])')
a.Define('ddt_discr','DDT_discr(f, Dijet_pt, Dijet_msoftdrop)')

a.Snapshot(['ddt_discr0','ddt_discr1','ddt_discr','Dijet_deepTagMD_TvsQCD','Dijet_deepTag_TvsQCD','Dijet_particleNet_TvsQCD','Dijet_msoftdrop'], '{}_ddt_out.root'.format(proc),'Events')

