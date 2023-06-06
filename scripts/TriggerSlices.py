import sys, time, ROOT
from collections import OrderedDict

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp
from THClass import THClass

def MakeEfficiency(year, HT=0):
    if year == '17B':
        fName = 'dijet_nano/SingleMuonDataB_17_snapshot.txt'
    elif year == '17All':
        fName = 'dijet_nano/SingleMuonDataWithB_17_snapshot.txt'
    else:
        fName = 'dijet_nano/SingleMuonData_{}_snapshot.txt'.format(year)

    selection = THClass(fName,year if 'B' not in year else '17',1,1)
    selection.OpenForSelection('None')
    hists = HistGroup('out')

    # HT cut
    before = selection.a.DataFrame.Count()
    selection.a.Cut('HT_cut', 'HT > {}'.format(HT))
    after = selection.a.DataFrame.Count()

    noTag = selection.a.Cut('pretrig','HLT_Mu50==1')

    # baseline before tagging. make coarsely- and finely-binned histos
    hists.Add('CoarseDenominator',selection.a.DataFrame.Histo2D(('CoarseDenominator','',10,60,260,11,800,3000),'m_javg','mth_trig'))
    hists.Add('FineDenominator',selection.a.DataFrame.Histo2D(('CoarseDenominator','',20,60,260,22,800,3000),'m_javg','mth_trig'))
    selection.ApplyTrigs()
    hists.Add('CoarseNumerator',selection.a.DataFrame.Histo2D(('CoarseNumerator','',10,60,260,11,800,3000),'m_javg','mth_trig'))
    hists.Add('FineNumerator',selection.a.DataFrame.Histo2D(('FineNumerator','',20,60,260,22,800,3000),'m_javg','mth_trig'))

    # Make efficiencies
    effs = {
	'Coarse': ROOT.TEfficiency(hists['CoarseNumerator'],hists['CoarseDenominator']),
	'Fine': ROOT.TEfficiency(hists['FineNumerator'],hists['FineDenominator'])
    }

    out = ROOT.TFile.Open('TriggerSlices_{}_{}.root'.format(year,HT),'RECREATE')
    out.cd()

    for name, eff in effs.items():
	# create the 2D histogram
	g = eff.CreateHistogram()
	g.SetName(name+'_hist')
	g.SetTitle(name)
        g.GetXaxis().SetTitle('m_{j}^{avg} (GeV)')
        g.GetYaxis().SetTitle('m_{jj} (GeV)')
        g.GetZaxis().SetTitle('Efficiency')
        g.SetMinimum(0.0)
        g.SetMaximum(1.0)
	g.Write()
	eff.SetName(name)
	eff.Write()
	# Now make slices
	for nx in range(1,g.GetNbinsX()):
	    clone = g.Clone('m_X slice {}'.format(nx))
	    clone.GetXaxis().SetRange(nx,nx)
	    ySlice = clone.ProjectionY()
	    if name=='Coarse':
	    	f = ROOT.TF1('eff_mX_slice{}'.format(nx),'([0]/(1+ TMath::Exp(-[1]*(x-[2]))))',11,800,3000)
	    else:
		f = ROOT.TF1('eff_mX_slice{}'.format(nx),'([0]/(1+ TMath::Exp(-[1]*(x-[2]))))',22,800,3000)
	    f.SetParameter(0,1)
	    f.SetParameter(1,80)
	    f.SetParameter(2,1000)
	    f.SetParLimits(0,0.95,1.05)
	    f.SetParLimits(1,50,200)
	    f.SetParLimits(2,900,1100)
	    ySlice.Fit(f)
	    ySlice.SetName('{}_mXslice{}_hist'.format(name,nx))
	    ySlice.Write()

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

    if not args.recycle:
    	for year in ['16','17','17B','18']:
	    MakeEfficiency(year,args.HT)

    files = {
        '16': ROOT.TFile.Open('TriggerSlices_16_{}.root'.format(args.HT)),
        '17': ROOT.TFile.Open('TriggerSlices_17_{}.root'.format(args.HT)),
        '18': ROOT.TFile.Open('TriggerSlices_18_{}.root'.format(args.HT)),
        '17B': ROOT.TFile.Open('TriggerSlices_17B_{}.root'.format(args.HT))
    }

    hists = {hname.GetName():[files[y].Get(hname.GetName()) for y in ['17']] for hname in files['16'].GetListOfKeys() if 'slice' in hname.GetName()}

    for hname in hists.keys():
	c = ROOT.TCanvas('c','c')
	for i,h in enumerate(hists[hname]):
            h.SetTitle('')
            h.GetXaxis().SetTitle('m_{jj}')
            h.GetYaxis().SetTitle('Efficiency')
            if i == 0:
                h.Draw('APE')
            else:
                h.Draw('same PE')

	c.Print('plots/TriggerSlice_{}_HT{}.png'.format(hname,args.HT))
