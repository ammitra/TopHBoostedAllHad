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
    # The dijet_nano/get_all.py script ensures that the 2017B run is not included in both `Data_17_snapshot.txt` and 
    # `SingleMuonData_17_snapshot.txt`
    # We must also evaluate the 2017C, 2017D, 2017E and 2017F datasets combined together, since they share triggers which
    # result in higher efficiencies than with the inclusion of the 2017B dataset.
    if year == '17B':
	fName = 'dijet_nano/SingleMuonDataB_17_snapshot.txt'
    elif year == '17All':
	fName = 'dijet_nano/SingleMuonDataWithB_17_snapshot.txt'
    else:
	fName = 'dijet_nano/SingleMuonData_{}_snapshot.txt'.format(year)

    print('Opening {}'.format(fName.split('/')[-1]))

    selection = THClass(fName,year if year.isdigit() else '17',1,1)
    selection.OpenForSelection('None')
    hists = HistGroup('out')

    # keep track of total efficiency to see how HT cut affects it
    before = selection.a.DataFrame.Count()
    # cut on HT to improve trigger efficiency
    selection.a.Cut('HT_cut', 'HT > {}'.format(HT))
    after = selection.a.DataFrame.Count()
    
    noTag = selection.a.Cut('pretrig','HLT_Mu50==1')

    # Baseline - no tagging
    hists.Add('preTagDenominator',selection.a.DataFrame.Histo1D(('preTagDenominator','',22,800,3000),'mth_trig'))
    hists.Add('preTagDenominator_mjavg',selection.a.DataFrame.Histo1D(('preTagDenominator','',20,0,500),'m_javg'))
    hists.Add('preTagDenominator_HT',selection.a.DataFrame.Histo1D(('preTagDenominator','',20,0,3000),'HT'))
    selection.ApplyTrigs()
    hists.Add('preTagNumerator',selection.a.DataFrame.Histo1D(('preTagNumerator','',22,800,3000),'mth_trig'))
    hists.Add('preTagNumerator_mjavg',selection.a.DataFrame.Histo1D(('preTagNumerator','',20,0,500),'m_javg'))
    hists.Add('preTagNumerator_HT',selection.a.DataFrame.Histo1D(('preTagNumerator','',20,0,3000),'HT'))

    # Make efficieincies
    effs = {
        "Pretag": ROOT.TEfficiency(hists['preTagNumerator'], hists['preTagDenominator']),
	"Pretag_mjavg": ROOT.TEfficiency(hists['preTagNumerator_mjavg'], hists['preTagDenominator_mjavg']),
	"Pretag_HT":ROOT.TEfficiency(hists['preTagNumerator_HT'], hists['preTagDenominator_HT'])
    }

    out = ROOT.TFile.Open('triggers/THtrigger_HT{}_{}.root'.format(HT,year),'RECREATE')
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

    before = before.GetValue()
    after = after.GetValue()
    print('------------------------------------------------------------')
    print('Cut on HT > {} removes {}% of SingleMuon data'.format(HT, 100.*(1.-(float(after)/float(before)))))
    print('------------------------------------------------------------')

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--HT', type=str, dest='HT',
			action='store', default='0',
			 help='Value of HT to cut on')
    args = parser.parse_args()

    start = time.time()
    CompileCpp('THmodules.cc')
    for y in ['16','17','17B','17All','18']:
        MakeEfficiency(y, args.HT)

    files = {
        '16': ROOT.TFile.Open('triggers/THtrigger_HT{}_16.root'.format(args.HT)),
        '17': ROOT.TFile.Open('triggers/THtrigger_HT{}_17.root'.format(args.HT)),	 # contains 2017 C, D, E, F
        '18': ROOT.TFile.Open('triggers/THtrigger_HT{}_18.root'.format(args.HT)),
	'17B': ROOT.TFile.Open('triggers/THtrigger_HT{}_17B.root'.format(args.HT)),	 # contains 2017 B
	'17All': ROOT.TFile.Open('triggers/THtrigger_HT{}_17All.root'.format(args.HT))    # contains 2017 B, C, D, E, F
    }

    hists = {hname.GetName():[files[y].Get(hname.GetName()) for y in ['16','17','18']] for hname in files['16'].GetListOfKeys() if '_graph' in hname.GetName()}
    colors = [ROOT.kBlack, ROOT.kGreen+1, ROOT.kOrange-3]
    legendNames = ['2016','2017','2018']
    for hname in hists.keys():
        c = ROOT.TCanvas('c','c',800,700)
        leg = ROOT.TLegend(0.7,0.5,0.88,0.7)
        for i,h in enumerate(hists[hname]):
            h.SetLineColor(colors[i])
            h.SetTitle('')
            h.GetXaxis().SetTitle('m_{jj}' if 'avg' not in hname else 'm_{j}^{avg}')
            h.GetYaxis().SetTitle('Efficiency')
            if i == 0:
                h.Draw('AP')
            else:
                h.Draw('same P')
            
            leg.AddEntry(h,legendNames[i],'pe')

        leg.Draw()
        c.Print('plots/Trigger_{}_HT{}.pdf'.format(hname,args.HT),'pdf')

    c.Clear()
    # Now compare just 2017 total (B,C,D,E,F) and 2017 later (C, D, E, F)
    leg2 = ROOT.TLegend(0.7,0.5,0.88,0.7)
    # total 2017 minus 2017B
    h17 = files['17'].Get('Pretag_graph')
    h17.SetLineColor(ROOT.kGreen)
    h17.SetTitle('')
    h17.GetXaxis().SetTitle('m_{jj}')
    h17.GetYaxis().SetTitle('Efficiency')
    h17.Draw('AP')
    leg2.AddEntry(h17, 'later 2017', 'pe') 

    # only 2017B
    h17B = files['17B'].Get('Pretag_graph')
    h17B.SetLineColor(ROOT.kBlack)
    h17B.SetTitle('')
    h17B.GetXaxis().SetTitle('m_{jj}')
    h17B.GetYaxis().SetTitle('Efficiency')
    h17B.Draw('same P')
    leg2.AddEntry(h17B, 'full 2017', 'pe')

    leg2.Draw()
    c.Print('plots/Trigger_2017Full_vs_2017Later_HT{}.pdf'.format(args.HT))

    print ('%s sec'%(time.time()-start))
