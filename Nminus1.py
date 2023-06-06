import ROOT, time
ROOT.gROOT.SetBatch(True)
from TIMBER.Tools.Common import CompileCpp
from TIMBER.Analyzer import analyzer, HistGroup, VarGroup, CutGroup
from argparse import ArgumentParser
from THClass import THClass

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

flags = [
    'Flag_goodVertices',
    'Flag_globalSuperTightHalo2016Filter',
    'Flag_HBHENoiseFilter',
    'Flag_HBHENoiseIsoFilter',
    'Flag_EcalDeadCellTriggerPrimitiveFilter',
    'Flag_BadPFMuonFilter',
    'Flag_BadPFMuonDzFilter',
    'Flag_eeBadScFilter'
]

# Recommended selection 
MET_filters = selection.a.GetFlagString(flags)
selection.a.Cut('flags', MET_filters)
selection.a.Cut('jetId', 'Jet_jetId[0] > 1 && Jet_jetId[1] > 1')
selection.a.Define('DijetIdxs','PickDijetsNminus1(FatJet_phi)')
selection.a.Cut('dijetsExist','DijetIdxs[0] > -1 && DijetIdxs[1] > -1')
selection.a.SubCollection('Dijet','FatJet','DijetIdxs',useTake=True)
norm = selection.GetXsecScale()
selection.a.Define('norm',str(norm))

# VarGroup to store info about jets
jets = VarGroup('Dijets')
jets.Add('lead_vect',"hardware::TLvector(Dijet_pt[0], Dijet_eta[0], Dijet_phi[0], Dijet_msoftdrop[0])")
jets.Add('sublead_vect','hardware::TLvector(Dijet_pt[1], Dijet_eta[1], Dijet_phi[1], Dijet_msoftdrop[1])')
jets.Add('deltaEta', 'abs(lead_vect.Eta() - sublead_vect.Eta())')
jets.Add('mtphi','hardware::InvariantMass({lead_vect,sublead_vect})')

# Plotting variables
plotting_vars = VarGroup('plotting_vars')
plotting_vars.Add('mtop','Dijet_msoftdrop[0]')
plotting_vars.Add('mphi','Dijet_msoftdrop[1]')

# N-1 cuts to make
NCuts = CutGroup('NCuts')
NCuts.Add('deltaEta_cut','deltaEta < 1.6')
NCuts.Add('pt_cut','Dijet_pt[0] > 350 && Dijet_pt[1] > 350')
NCuts.Add('absEta_cut','abs(Dijet_eta[0]) < 2.4 && abs(Dijet_eta[1]) < 2.4')
NCuts.Add('mSD_cut','Dijet_msoftdrop[0] > 50 && Dijet_msoftdrop[1] > 50')
# dummy cuts so we can plot values of interest
NCuts.Add('mtop_cut','mtop > 0')
NCuts.Add('mphi_cut','mphi > 0')
NCuts.Add('mtphi_cut','mtphi > 0')

nodeToPlot = selection.a.Apply([jets,plotting_vars])
nminus1Nodes = selection.a.Nminus1(NCuts, node=nodeToPlot)
nminus1Hists = HistGroup('nminus1Hists')

oFile = ROOT.TFile.Open('rootfiles/NMinus1_{}_{}_{}of{}.root'.format(args.setname, args.era, args.ijob, args.njobs),'RECREATE')
oFile.cd()
binning = {
    'mtop':[25,50,300],
    'mtphi':[25,800,2200],
    'mphi':[25,50,270],
    'deltaEta':[20,0,2.0]
}

print('Plotting')
print(nminus1Nodes)
for nkey in nminus1Nodes.keys():
    if nkey=='full': continue
    print('\t{}'.format(nkey))
    if ('mtop' not in nkey) and ('mphi' not in nkey) and ('mtphi' not in nkey) and ('deltaEta' not in nkey):
	continue	
    var = nkey.replace('_cut','').replace('minus_','')
    hist_tuple = (var,var,binning[var][0],binning[var][1],binning[var][2])
    hist = nminus1Nodes[nkey].DataFrame.Histo1D(hist_tuple,var,'norm')
    hist.GetValue()
    nminus1Hists.Add(var,hist)

nminus1Hists.Do('Write')
oFile.Close()

print ('%s sec'%(time.time()-start))
