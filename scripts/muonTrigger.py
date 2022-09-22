import sys, time, ROOT
from collections import OrderedDict

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp
from THClass import THClass

def ApplyTrigs(ana, year):
    trigs = {
	16:['HLT_PFHT800','HLT_PFHT650_WideJetMJJ900DEtaJJ1p5','HLT_PFHT900','HLT_AK8PFJet450'],
	17:['HLT_PFHT1050','HLT_AK8PFJet500','HLT_AK8PFHT750_TrimMass50','HLT_AK8PFHT800_TrimMass50','HLT_AK8PFJet400_TrimMass30'],
	18:['HLT_PFHT1050','HLT_AK8PFHT800_TrimMass50','HLT_AK8PFJet500','HLT_AK8PFJet400_TrimMass30']
    }
    ana.Cut('trigger', ana.GetTriggerString(trigs[year]))
    return ana.GetActiveNode()

def MakeEfficiency(year):
    selection = THClass('dijet_nano/Data_{}_snapshot.txt'.format(year),year,1,1)
    selection.OpenForSelection('None')
    # selection.a.Define('mth_trig','hardware::InvariantMass(Dijet_vect)')
    # selection.a.Cut('morePt','ROOT::VecOps::All(Dijet_pt > 400)')
    hists = HistGroup('out')

    #noTag = selection.a.Cut('pretrig','HLT_PFJet320==1')
    noTag = selection.a.Cut('pretrig','HLT_Mu50==1')

    # Baseline - no tagging
    hists.Add('preTagDenominator',selection.a.DataFrame.Histo1D(('preTagDenominator','',22,800,3000),'mth_trig'))
    ApplyTrigs(selection.a,year)
    hists.Add('preTagNumerator',selection.a.DataFrame.Histo1D(('preTagNumerator','',22,800,3000),'mth_trig'))

    '''
    # DeepAK8 SR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('deepTag_TvsQCD')
    hists.Add('postTagDenominator_DAK8_SR',selection.a.DataFrame.Histo1D(('postTagDenominator_DAK8_SR','',22,800,3000),'mth_trig'))
    ApplyTrigs(selection.a,year)
    hists.Add('preTagNumerator_DAK8_SR',selection.a.DataFrame.Histo1D(('preTagNumerator_DAK8_SR','',22,800,3000),'mth_trig'))
    # DeepAK8 CR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('deepTag_TvsQCD',invert=True)
    hists.Add('postTagDenominator_DAK8_CR',selection.a.DataFrame.Histo1D(('postTagDenominator_DAK8_CR','',22,800,3000),'mth_trig'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_DAK8_CR',selection.a.DataFrame.Histo1D(('preTagNumerator_DAK8_CR','',22,800,3000),'mth_trig'))
    '''

    # ParticleNet SR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('particleNet_TvsQCD')
    hists.Add('postTagDenominator_PN_SR',selection.a.DataFrame.Histo1D(('postTagDenominator_PN_SR','',22,800,3000),'mth_trig'))
    ApplyTrigs(selection.a,year)
    hists.Add('preTagNumerator_PN_SR',selection.a.DataFrame.Histo1D(('preTagNumerator_PN_SR','',22,800,3000),'mth_trig'))

    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('particleNet_TvsQCD',invert=True)
    hists.Add('postTagDenominator_PN_CR',selection.a.DataFrame.Histo1D(('postTagDenominator_PN_CR','',22,800,3000),'mth_trig'))
    ApplyTrigs(selection.a,year)
    hists.Add('preTagNumerator_PN_CR',selection.a.DataFrame.Histo1D(('preTagNumerator_PN_CR','',22,800,3000),'mth_trig'))

    # Make efficieincies
    effs = {
        "Pretag": ROOT.TEfficiency(hists['preTagNumerator'], hists['preTagDenominator']),
        "PN_SR": ROOT.TEfficiency(hists['preTagNumerator_PN_SR'], hists['postTagDenominator_PN_SR']),
        "PN_CR": ROOT.TEfficiency(hists['preTagNumerator_PN_CR'], hists['postTagDenominator_PN_CR'])
    }

    out = ROOT.TFile.Open('THtrigger_%s.root'%year,'RECREATE')
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

    hists = {hname.GetName():[files[y].Get(hname.GetName()) for y in [16,17,18]] for hname in files[16].GetListOfKeys() if '_graph' in hname.GetName()}
    colors = [ROOT.kBlack, ROOT.kGreen+1, ROOT.kOrange-3]
    legendNames = ['2016','2017','2018']
    for hname in hists.keys():
        c = ROOT.TCanvas('c','c',800,700)
        leg = ROOT.TLegend(0.7,0.5,0.88,0.7)
        for i,h in enumerate(hists[hname]):
            h.SetLineColor(colors[i])
            h.SetTitle('')
            h.GetXaxis().SetTitle('m_{jj}')
            h.GetYaxis().SetTitle('Efficiency')
            if i == 0:
                h.Draw('AP')
            else:
                h.Draw('same P')
            
            leg.AddEntry(h,legendNames[i],'pe')

        leg.Draw()
        c.Print('plots/Trigger_%s.pdf'%hname,'pdf')

    print ('%s sec'%(time.time()-start))
