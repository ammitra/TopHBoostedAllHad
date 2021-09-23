import sys, time, ROOT
from collections import OrderedDict

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp
from THClass import THClass

def MakeEfficiency(year):
    selection = THClass('../dijet_nano_files/THsnapshot_Data_%s.root'%(year),year,1,1)
    selection.OpenForSelection('None')
    # selection.a.Define('mth_trig','hardware::InvariantMass(Dijet_vect)')
    # selection.a.Define('m_javg','(Dijet_msoftdrop[0]+Dijet_msoftdrop[0])/2')
    # selection.a.Cut('morePt','ROOT::VecOps::All(Dijet_pt > 400)')
    hists = HistGroup('out')

    noTag = selection.a.Cut('pretrig','HLT_PFJet320==1')

    # Baseline - no tagging
    hists.Add('preTagDenominator',selection.a.DataFrame.Histo2D(('preTagDenominator','',20,60,260,22,800,3000),'m_javg','mth_trig'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator',selection.a.DataFrame.Histo2D(('preTagNumerator','',20,60,260,22,800,3000),'m_javg','mth_trig'))

    # DeepAK8 SR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('deepTag_TvsQCD')
    hists.Add('postTagDenominator_DAK8_SR',selection.a.DataFrame.Histo2D(('postTagDenominator_DAK8_SR','',20,60,260,22,800,3000),'m_javg','mth_trig'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_DAK8_SR',selection.a.DataFrame.Histo2D(('preTagNumerator_DAK8_SR','',20,60,260,22,800,3000),'m_javg','mth_trig'))
    # DeepAK8 CR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('deepTag_TvsQCD',invert=True)
    hists.Add('postTagDenominator_DAK8_CR',selection.a.DataFrame.Histo2D(('postTagDenominator_DAK8_CR','',20,60,260,22,800,3000),'m_javg','mth_trig'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_DAK8_CR',selection.a.DataFrame.Histo2D(('preTagNumerator_DAK8_CR','',20,60,260,22,800,3000),'m_javg','mth_trig'))

    # ParticleNet SR
    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('particleNet_TvsQCD')
    hists.Add('postTagDenominator_PN_SR',selection.a.DataFrame.Histo2D(('postTagDenominator_PN_SR','',20,60,260,22,800,3000),'m_javg','mth_trig'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_PN_SR',selection.a.DataFrame.Histo2D(('preTagNumerator_PN_SR','',20,60,260,22,800,3000),'m_javg','mth_trig'))

    selection.a.SetActiveNode(noTag)
    selection.ApplyTopPick('particleNet_TvsQCD',invert=True)
    hists.Add('postTagDenominator_PN_CR',selection.a.DataFrame.Histo2D(('postTagDenominator_PN_CR','',20,60,260,22,800,3000),'m_javg','mth_trig'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator_PN_CR',selection.a.DataFrame.Histo2D(('preTagNumerator_PN_CR','',20,60,260,22,800,3000),'m_javg','mth_trig'))

    # Make efficieincies
    effs = {
        "Pretag": ROOT.TEfficiency(hists['preTagNumerator'], hists['preTagDenominator']),
        "DAK8_SR": ROOT.TEfficiency(hists['preTagNumerator_DAK8_SR'], hists['postTagDenominator_DAK8_SR']),
        "DAK8_CR": ROOT.TEfficiency(hists['preTagNumerator_DAK8_CR'], hists['postTagDenominator_DAK8_CR']),
        "PN_SR": ROOT.TEfficiency(hists['preTagNumerator_PN_SR'], hists['postTagDenominator_PN_SR']),
        "PN_CR": ROOT.TEfficiency(hists['preTagNumerator_PN_CR'], hists['postTagDenominator_PN_CR'])
    }

    out = ROOT.TFile.Open('THtrigger2D_%s.root'%year,'RECREATE')
    out.cd()
    for name,eff in effs.items():
        g = eff.CreateHistogram()
        g.SetName(name+'_hist')
        g.SetTitle(name)
        g.GetXaxis().SetTitle('m_{j}^{avg} (GeV)')
        g.GetYaxis().SetTitle('m_{jj} (GeV)')
        g.GetZaxis().SetTitle('Efficiency')
        g.SetMinimum(0.6)
        g.SetMaximum(1.0)
        f = ROOT.TF2("eff_func","1-[0]/10*exp([1]*y/1000)*exp([2]*x/200)",60,260,800,2600)
        f.SetParameter(0,1)
        f.SetParameter(1,-2)
        f.SetParameter(2,-2)
        g.Fit(f)
        g.Write()
        eff.SetName(name)
        eff.Write()
    out.Close()

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--recycle', dest='recycle',
                        action='store_true', default=False,
                        help='Recycle existing files and just plot.')
    args = parser.parse_args()
    start = time.time()
    CompileCpp('THmodules.cc')
    if not args.recycle:
        for y in [16,17,18]:
            MakeEfficiency(y)

    files = {
        16: ROOT.TFile.Open('THtrigger2D_16.root'),
        17: ROOT.TFile.Open('THtrigger2D_17.root'),
        18: ROOT.TFile.Open('THtrigger2D_18.root')
    }

    hists = {hname.GetName():[files[y].Get(hname.GetName()) for y in [16,17,18]] for hname in files[16].GetListOfKeys() if '_hist' in hname.GetName()}
    colors = [ROOT.kBlack, ROOT.kGreen+1, ROOT.kOrange-3]
    legendNames = ['2016','2017','2018']
    for hname in hists.keys():
        c = ROOT.TCanvas('c','c',2000,700)
        c.Divide(3,1)
        for i,h in enumerate(hists[hname]):
            c.cd(i+1)
            ROOT.gPad.SetLeftMargin(0.13)
            ROOT.gPad.SetRightMargin(0.16)
            h.GetZaxis().SetTitleOffset(1.7)
            h.SetLineColor(colors[i])
            h.SetTitle(legendNames[i])
            h.Draw('colz')

        c.Print('plots/Trigger2D_%s.pdf'%hname,'pdf')

    print ('%s sec'%(time.time()-start))
