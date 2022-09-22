import sys, time, ROOT
from collections import OrderedDict

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp, OpenJSON
from THClass import THClass

'''
Script for creating the trigger efficiencies per year based on the subyears, with the updated triggers found through scripts/trigTest.py and located in THconfig.json
'''

def makeEfficiency(subyear):
    '''
	subyear str = the subyears found in THconfig.json
	e.g. DataH_16
    '''
    year = subyear.split("_")[-1]
    selection = THClass('dijet_nano/{}_snapshot.txt'.format(subyear),year,1,1)
    selection.OpenForSelection('None')
    hists = HistGroup('out')

    # use orthogonal trig for noTag
    noTag = selection.a.Cut('pretrig','HLT_Mu50==1')

    # baseline - no tagging
    hists.Add('preTagDenominator',selection.a.DataFrame.Histo1D(('preTagDenominator','',22,800,3000),'mth_trig'))
    selection.ApplyNewTrigs(subyear)
    hists.Add('preTagNumerator',selection.a.DataFrame.Histo1D(('preTagNumerator','',22,800,3000),'mth_trig'))

    # ParticleNet SR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('particleNet_TvsQCD', invert=False, CRv2='particleNet_TvsQCD')
    hists.Add('postTagDenominator_PN_SR',selection.a.DataFrame.Histo1D(('postTagDenominator_PN_SR','',22,800,3000),'mth_trig'))
    selection.ApplyNewTrigs(subyear)
    hists.Add('preTagNumerator_PN_SR',selection.a.DataFrame.Histo1D(('preTagNumerator_PN_SR','',22,800,3000),'mth_trig'))

    # ParticleNet CR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('particleNet_TvsQCD',invert=True, CRv2='particleNet_TvsQCD')
    hists.Add('postTagDenominator_PN_CR',selection.a.DataFrame.Histo1D(('postTagDenominator_PN_CR','',22,800,3000),'mth_trig'))
    selection.ApplyNewTrigs(subyear)
    hists.Add('preTagNumerator_PN_CR',selection.a.DataFrame.Histo1D(('preTagNumerator_PN_CR','',22,800,3000),'mth_trig'))

    # make efficiencies
    effs = {
        "Pretag": ROOT.TEfficiency(hists['preTagNumerator'], hists['preTagDenominator']),
        "PN_SR": ROOT.TEfficiency(hists['preTagNumerator_PN_SR'], hists['postTagDenominator_PN_SR']),
        "PN_CR": ROOT.TEfficiency(hists['preTagNumerator_PN_CR'], hists['postTagDenominator_PN_CR'])
    }

    out = ROOT.TFile.Open('THtrigger_{}.root'.format(subyear),'RECREATE')
    out.cd()

    for name,eff in effs.items():
        f = ROOT.TF1("eff_func","-[0]/10*exp([1]*x/1000)+1",800,2600)
        f.SetParameter(0,1)
        f.SetParameter(1,-2)
        eff.Fit(f)
        eff.Write()
        g = eff.CreateGraph()
        g.SetName(name+'_graph')
        g.SetTitle(name)
        g.SetMinimum(0.5)
        g.SetMaximum(1.01)
        g.Write()
    out.Close()

if __name__ == "__main__":
    start = time.time()
    CompileCpp('THmodules.cc')

    # get the subyears from JSON
    config = OpenJSON('THconfig.json')
    trigs = config['TRIGS']	# dict with {subyear: [trigs]}, note trigs are unicode, converted in ApplyNewTrigs()
    subyears = trigs.keys()	# list of subyear names, ascii encoded
    '''
    for subyear in subyears:
	makeEfficiency(subyear)
    '''

    # dict of {subyear: rootfile}
    files = {subyear: ROOT.TFile.Open('THtrigger_{}.root'.format(subyear)) for subyear in subyears}
    # dict of {histname: [hist_year1, hist_year2, ...]}
    hists = {hname.GetName():[f[y].Get(hname.GetName()) for y in subyears] for hname in files['DataG_16'].GetListOfKeys() if '_graph' in hname.GetName()}


















