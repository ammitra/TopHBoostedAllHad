'''
Calculates efficiencies of a chosen tagger (particleNetMD Hbb or Wqq) in selecting a given flavor of jet (Wqq, Hbb, Top, or unmerged) at a given working point
Should work on signal and ttbar
'''

import ROOT
from TIMBER.Analyzer import Correction, HistGroup, CutGroup, VarGroup, ModuleWorker, analyzer
from TIMBER.Tools.Common import CompileCpp, OpenJSON
from TIMBER.Tools.AutoPU import ApplyPU
from JMEvalsOnly import JMEvalsOnly
import TIMBER.Tools.AutoJME as AutoJME
from collections import OrderedDict
from THClass import THClass

def make_ratio_hist(histN,histD):
    print('Making ratio histogram')
    ratio_hist = histN.Clone('ratio_hist') #New histogram - ratio of (tagged jets)/(all jets) per bin
    #Loop over all bins, manually calculate ratios + set the bin contents of new histogram (I don't think there is a better way to do this for TH2?)
    for x in range(1,ratio_hist.GetNbinsX()+1):
        for y in range(1,ratio_hist.GetNbinsY()+1):
            val_tagged = histN.GetBinContent(x,y)
            val_all = histD.GetBinContent(x,y)
            if val_all == 0:
                ratio = 0
            else:
                ratio = val_tagged/val_all
            ratio_hist.SetBinContent(x,y,ratio)
    return ratio_hist

def MakeEfficiencyMaps(ana, tagger, wp):
    # First do the different top merging (first 4) and signal (last) cases
    ana.a.SubCollection('TopMerged_jets_all','Dijet','Dijet_jetFlavor_ttbar == 0')
    ana.a.SubCollection('WMerged_jets_all',  'Dijet','Dijet_jetFlavor_ttbar == 1')
    ana.a.SubCollection('bqMerged_jets_all', 'Dijet','Dijet_jetFlavor_ttbar == 2')
    ana.a.SubCollection('UnMerged_jets_all', 'Dijet','Dijet_jetFlavor_ttbar == 3')
    ana.a.SubCollection('HbbMerged_jets_all','Dijet','Dijet_jetFlavor_signal == 4')
    # Now check which ones are actually tagged by the tagger. 
    condition = '%s > %s'%(tagger,wp)
    tagged_by = 'tagged'
    ana.a.SubCollection('TopMerged_jets_%s'%tagged_by,'Dijet','Dijet_jetFlavor_ttbar == 0 && %s'%condition)
    ana.a.SubCollection('WMerged_jets_%s'%tagged_by,  'Dijet','Dijet_jetFlavor_ttbar == 1 && %s'%condition)
    ana.a.SubCollection('bqMerged_jets_%s'%tagged_by, 'Dijet','Dijet_jetFlavor_ttbar == 2 && %s'%condition)
    ana.a.SubCollection('UnMerged_jets_%s'%tagged_by, 'Dijet','Dijet_jetFlavor_ttbar == 3 && %s'%condition)
    ana.a.SubCollection('HbbMerged_jets_%s'%tagged_by,'Dijet','Dijet_jetFlavor_signal == 4 && %s'%condition)

    # Book a HistGroup to store all the histograms and ratios
    histgroup = HistGroup('Efficiencies')
    for collection in ['TopMerged_jets','WMerged_jets','bqMerged_jets','UnMerged_jets','HbbMerged_jets']:
	print('Calculating efficiencies for %s tagged by %s'%(collection, tagger))
	hist_all = ana.a.DataFrame.Histo2D(
	    ('%s_all'%collection,'%s_all'%collection,60,0,3000,12,-2.4,2.4),
	    '%s_all_pt_corr'%collection,
	    '%s_all_eta'%collection,
	    'weight__nominal'
	)
	hist_tag = ana.a.DataFrame.Histo2D(
	    ('%s_%s'%(collection,tagged_by),'%s_%s'%(collection,tagged_by),60,0,3000,12,-2.4,2.4),
            '%s_%s_pt_corr'%(collection,tagged_by),
            '%s_%s_eta'%(collection,tagged_by),
            'weight__nominal'
	)

	histgroup.Add('%s_all'%collection, hist_all)
	histgroup.Add('%s_tagged'%collection, hist_tag)

	ratio_eff  = ROOT.TEfficiency(histgroup['%s_tagged'%collection],histgroup['%s_all'%collection])
	ratio_hist = ratio_eff.CreateHistogram()
	ratio_hist.SetTitle('%s_tagged_to_all_ratio'%collection)
	ratio_hist.SetName('%s_tagged_to_all_ratio'%collection)
	histgroup.Add('%s_tagged_to_all_ratio'%collection, ratio_hist)

    # Save histograms out to file. 
    # Format will be <SETNAME>_<YEAR>_<TAGGER>_Efficiencies.root
    outName = 'ParticleNetSFs/EfficiencyMaps/%s_%s_%s_WP%s_Efficiencies.root'%(ana.setname,ana.year,tagger,str(wp).replace('.','p'))
    print('Saving histograms to %s'%(outName))
    outFile = ROOT.TFile.Open(outName, 'RECREATE')
    outFile.cd()
    histgroup.Do('Write')
    outFile.Close()


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='year',
                        action='store', required=True,
                        help='Year of set (16APV, 16, 17, 18).')
    '''
    parser.add_argument('-f', type=str, dest='flavor',
                        action='store', required=True,
                        help='Flavor of jets to target for efficiencies: "Hbb", "Wqq", "Top", or "UM" (unmerged)') 
    '''
    parser.add_argument('-t', type=str, dest='tagger',
                        help='Exact name of tagger discriminant, e.g "Dijet_particleNetMD_HbbvsQCD", "Dijet_particleNet_TvsQCD", "Dijet_deepTagMD_TvsQCD"',
                        action='store', required=True)
    parser.add_argument('-w', type=float, dest='wp', 
                        help='tagger working point',
                        action='store', required=True)
    args = parser.parse_args()

    CompileCpp('THmodules.cc')

    filename = 'dijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.year)
    selection = THClass('dijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.year),args.year,1,1)
    # This function will produce the 'Dijet_jetFlavor_ttbar/signal' column which provides an ID tag to MC jets from truth match
    selection.OpenForSelection('None')

    # Define MD-W tagger just in case
    selection.a.Define('Dijet_particleNetMD_WqqvsQCD','(Dijet_particleNetMD_Xqq+Dijet_particleNetMD_Xcc)/(Dijet_particleNetMD_Xqq+Dijet_particleNetMD_Xcc+Dijet_particleNetMD_QCD)')

    selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else str(selection.GetXsecScale()))
 
    MakeEfficiencyMaps(selection, args.tagger, args.wp)
