import sys, time, ROOT
from typing import OrderedDict

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp
from THClass import THClass

def MakeEfficiency(year):
    selection = THClass('../dijet_nano_files/THsnapshot_Data_%s.root'%(year),year,1,1)
    selection.OpenForSelection()
    selection.a.Define('mth','hardware::InvariantMass(Dijet_vect)')
    # selection.a.Cut('morePt','ROOT::VecOps::All(Dijet_pt > 400)')
    hists = HistGroup('out')

    noTag = selection.a.GetActiveNode()#Cut('pretrig','HLT_Mu50==1')

    # Baseline - no tagging
    hists.Add('preTagDenominator',selection.a.DataFrame.Histo1D(('preTagDenominator','',18,800,2600),'mth'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator',selection.a.DataFrame.Histo1D(('preTagNumerator','',18,800,2600),'mth'))

    # DeepAK8 SR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('deepTagMD_TvsQCD')
    hists.Add('postTagDenominator_DAK8_SR',selection.a.DataFrame.Histo1D(('postTagDenominator_DAK8_SR','',18,800,2600),'mth'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_DAK8_SR',selection.a.DataFrame.Histo1D(('preTagNumerator_DAK8_SR','',18,800,2600),'mth'))
    # DeepAK8 CR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('deepTagMD_TvsQCD',invert=True)
    hists.Add('postTagDenominator_DAK8_CR',selection.a.DataFrame.Histo1D(('postTagDenominator_DAK8_CR','',18,800,2600),'mth'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_DAK8_CR',selection.a.DataFrame.Histo1D(('preTagNumerator_DAK8_CR','',18,800,2600),'mth'))

    # ParticleNet SR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('particleNet_TvsQCD')
    hists.Add('postTagDenominator_PN_SR',selection.a.DataFrame.Histo1D(('postTagDenominator_PN_SR','',18,800,2600),'mth'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_PN_SR',selection.a.DataFrame.Histo1D(('preTagNumerator_PN_SR','',18,800,2600),'mth'))

    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('particleNet_TvsQCD',invert=True)
    hists.Add('postTagDenominator_PN_CR',selection.a.DataFrame.Histo1D(('postTagDenominator_PN_CR','',18,800,2600),'mth'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_PN_CR',selection.a.DataFrame.Histo1D(('preTagNumerator_PN_CR','',18,800,2600),'mth'))

    # Make efficieincies
    effs = {
        "Pretag": ROOT.TEfficiency(hists['preTagNumerator'], hists['preTagDenominator']),
        "DAK8_SR": ROOT.TEfficiency(hists['preTagNumerator_DAK8_SR'], hists['postTagDenominator_DAK8_SR']),
        "DAK8_CR": ROOT.TEfficiency(hists['preTagNumerator_DAK8_CR'], hists['postTagDenominator_DAK8_CR']),
        "PN_SR": ROOT.TEfficiency(hists['preTagNumerator_PN_SR'], hists['postTagDenominator_PN_SR']),
        "PN_CR": ROOT.TEfficiency(hists['preTagNumerator_PN_CR'], hists['postTagDenominator_PN_CR'])
    }

    out = ROOT.TFile.Open('THtrigger_%s.root'%year,'RECREATE')
    out.cd()
    for name,eff in effs.items():
        g = eff.CreateGraph()
        g.SetName(name)
        g.SetTitle(name)
        g.SetMinimum(0.5)
        g.SetMaximum(1.01)
        g.Write()
    out.Close()

if __name__ == '__main__':
    start = time.time()
    CompileCpp('THmodules.cc')
    for y in [16,17,18]:
        MakeEfficiency(y)

    files = {
        16: ROOT.TFile.Open('THtrigger_16.root'),
        17: ROOT.TFile.Open('THtrigger_17.root'),
        18: ROOT.TFile.Open('THtrigger_18.root')
    }

    hists = {hname.GetName():[files[y].Get(hname.GetName()) for y in [16,17,18]] for hname in files[16].GetListOfKeys()}
    colors = [ROOT.kBlack, ROOT.kGreen+1, ROOT.kOrange-3]
    legendNames = ['2016','2017','2018']
    for hname in hists.keys():
        c = ROOT.TCanvas('c','c',800,700)
        leg = ROOT.TLegend(0.7,0.5,0.88,0.7)
        for i,h in enumerate(hists[hname]):
            h.SetLineColor(colors[i])
            if i == 0:
                h.Draw('AP')
            else:
                h.Draw('same P')
            
            leg.AddEntry(h,legendNames[i],'pe')

        leg.Draw()
        c.Print('plots/Trigger_%s.pdf'%hname,'pdf')

    print ('%s sec'%(time.time()-start))