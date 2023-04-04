import sys, time, ROOT
from collections import OrderedDict

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp
from THClass import THClass

def MakeEfficiency(year, HT=0):
    '''
        year (str) : 16, 17, 17B, 17All, 18
	HT   (int) : value of HT to cut on
    '''
    # For measuring trigger efficiencies, we use the data from the orthogonal SingleMuon dataset
    # For 2017, we need to ensure that the 2017B dataset is evaluated separately and its own efficiency is generated
    # so that it may be applied to a fraction of the 2017 MC corresponding to the contribution of 2017B to the total
    # 2017 dataset.
    # We must also evaluate the 2017C, 2017D, 2017E and 2017F datasets combined together, since they share triggers which
    # result in higher efficiencies than with the inclusion of the 2017B dataset.
    if year == '17B':
	fName = 'dijet_nano/SingleMuonDataB_17_snapshot.txt'
    elif year == '17All':
        fName = 'dijet_nano/SingleMuonDataWithB_17_snapshot.txt'
    else:
	fName = 'dijet_nano/SingleMuonData_{}_snapshot.txt'.format(year)

    selection = THClass(fName,year if 'B' not in year else '17',1,1)
    selection.OpenForSelection('None')
    hists = HistGroup('out')

    # cut on HT to improve efficiency
    before = selection.a.DataFrame.Count()
    selection.a.Cut('HT_cut', 'HT > {}'.format(HT))
    after = selection.a.DataFrame.Count()

    noTag = selection.a.Cut('pretrig','HLT_Mu50==1')

    # Baseline - no tagging
    hists.Add('preTagDenominator',selection.a.DataFrame.Histo2D(('preTagDenominator','',20,60,260,22,800,3000),'m_javg','mth_trig'))
    hists.Add('preTagDenominatorZoomed', selection.a.DataFrame.Histo2D(('preTagDenominatorZoomed','',20,60,260,22,800,2000),'m_javg','mth_trig'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator',selection.a.DataFrame.Histo2D(('preTagNumerator','',20,60,260,22,800,3000),'m_javg','mth_trig'))
    hists.Add('preTagNumeratorZoomed', selection.a.DataFrame.Histo2D(('preTagNumeratorZoomed','',20,60,260,22,800,2000),'m_javg','mth_trig'))

    # make efficiencies
    effs = {
        "Pretag": ROOT.TEfficiency(hists['preTagNumerator'], hists['preTagDenominator']),
	"PretagZoom": ROOT.TEfficiency(hists['preTagNumeratorZoomed'], hists['preTagDenominatorZoomed']),
    }

    out = ROOT.TFile.Open('THtrigger2D_HT{}_{}.root'.format(HT,year), 'RECREATE')
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
	#f = ROOT.TF2("eff_func","1-[0]*exp([1]*y/1000)*exp([2]*x/200)",60,260,800,2600)
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
    parser.add_argument('--HT', type=str, dest='HT',
                        action='store', default='0',
                         help='Value of HT to cut on')
    parser.add_argument('--recycle', dest='recycle',
                        action='store_true', default=False,
                        help='Recycle existing files and just plot.')
    args = parser.parse_args()
    start = time.time()
    CompileCpp('THmodules.cc')
    if not args.recycle:
        for y in ['16','17','17B','18']:
            MakeEfficiency(y, args.HT)

    files = {
        '16': ROOT.TFile.Open('THtrigger2D_HT{}_16.root'.format(args.HT)),
        '17': ROOT.TFile.Open('THtrigger2D_HT{}_17.root'.format(args.HT)),
        '18': ROOT.TFile.Open('THtrigger2D_HT{}_18.root'.format(args.HT)),
	'17B': ROOT.TFile.Open('THtrigger2D_HT{}_17B.root'.format(args.HT)),
	'17All': ROOT.TFile.Open('THtrigger2D_HT{}_17All.root'.format(args.HT))
    }

    hists = {hname.GetName():[files[y].Get(hname.GetName()) for y in ['16','17','18']] for hname in files['16'].GetListOfKeys() if '_hist' in hname.GetName()}
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

        c.Print('plots/Trigger2D_{}_HT{}.pdf'.format(hname, args.HT),'pdf')

    print ('%s sec'%(time.time()-start))
