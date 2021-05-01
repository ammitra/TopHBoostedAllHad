import sys, time, ROOT
from typing import OrderedDict

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp
from THClass import THClass

def MakeEfficiency(year):
    selection = THClass('../dijet_nano_files/THsnapshot_Data_%s.root'%(year),year,1,1)
    selection.OpenForSelection()
    selection.a.Define('mth','hardware::InvariantMass(Dijet_vect)')
    selection.a.Define('m_javg','(Dijet_msoftdrop_corr[0]+Dijet_msoftdrop_corr[0])/2')
    # selection.a.Cut('morePt','ROOT::VecOps::All(Dijet_pt > 400)')
    hists = HistGroup('out')

    noTag = selection.a.GetActiveNode()#Cut('pretrig','HLT_Mu50==1')

    # Baseline - no tagging
    hists.Add('preTagDenominator',selection.a.DataFrame.Histo2D(('preTagDenominator','',20,60,260,18,800,2600),'m_javg','mth'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator',selection.a.DataFrame.Histo2D(('preTagNumerator','',20,60,260,18,800,2600),'m_javg','mth'))

    # DeepAK8 SR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('deepTagMD_TvsQCD')
    hists.Add('postTagDenominator_DAK8_SR',selection.a.DataFrame.Histo2D(('postTagDenominator_DAK8_SR','',20,60,260,18,800,2600),'Higgs_msoftdrop_corr','mth'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_DAK8_SR',selection.a.DataFrame.Histo2D(('preTagNumerator_DAK8_SR','',20,60,260,18,800,2600),'Higgs_msoftdrop_corr','mth'))
    # DeepAK8 CR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('deepTagMD_TvsQCD',invert=True)
    hists.Add('postTagDenominator_DAK8_CR',selection.a.DataFrame.Histo2D(('postTagDenominator_DAK8_CR','',20,60,260,18,800,2600),'Higgs_msoftdrop_corr','mth'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_DAK8_CR',selection.a.DataFrame.Histo2D(('preTagNumerator_DAK8_CR','',20,60,260,18,800,2600),'Higgs_msoftdrop_corr','mth'))

    # ParticleNet SR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('particleNet_TvsQCD')
    hists.Add('postTagDenominator_PN_SR',selection.a.DataFrame.Histo2D(('postTagDenominator_PN_SR','',20,60,260,18,800,2600),'Higgs_msoftdrop_corr','mth'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_PN_SR',selection.a.DataFrame.Histo2D(('preTagNumerator_PN_SR','',20,60,260,18,800,2600),'Higgs_msoftdrop_corr','mth'))

    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('particleNet_TvsQCD',invert=True)
    hists.Add('postTagDenominator_PN_CR',selection.a.DataFrame.Histo2D(('postTagDenominator_PN_CR','',20,60,260,18,800,2600),'Higgs_msoftdrop_corr','mth'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_PN_CR',selection.a.DataFrame.Histo2D(('preTagNumerator_PN_CR','',20,60,260,18,800,2600),'Higgs_msoftdrop_corr','mth'))

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
        g = eff.CreateHistogram()
        g.SetName(name)
        g.SetTitle(name)
        g.GetXaxis().SetTitle('m_{H} (GeV)')
        g.GetYaxis().SetTitle('m_{tH} (GeV)')
        g.GetZaxis().SetTitle('Efficiency')
        g.SetMinimum(0.6)
        g.SetMaximum(1.0)
        g.Write()
        eff.SetName(name)
        eff.Write()
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
        c = ROOT.TCanvas('c','c',1600,700)
        c.Divide(3,1)
        for i,h in enumerate(hists[hname]):
            c.cd(i+1)
            h.SetLineColor(colors[i])
            h.SetTitle(h.GetTitle()+ ' - %s'%legendNames[i])
            h.Draw('colz')

        c.Print('plots/Trigger2D_%s.pdf'%hname,'pdf')

    print ('%s sec'%(time.time()-start))