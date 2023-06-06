import ROOT
from TIMBER.Analyzer import analyzer, HistGroup
from TIMBER.Tools.Plot import *
from collections import OrderedDict
import subprocess

ROOT.gROOT.SetBatch(True)

samples = {
    "ttbar" : "t#bar{t}",
    "QCD"   : "QCD",
    "ZJets" : "Z+jets",
    "WJets" : "W+jets"
}

signals = ['TprimeB-1200-{}'.format(mass) for mass in [125]]
for sig in signals:
    samples.update({sig:'({},{}) GeV'.format(*sig.split('-')[1:])})

colors = {}
for p in samples.keys():
    if 'Tprime' in p:
	colors[p] = ROOT.kCyan-int((int(p[-4:])-1400)/600)
    elif 'ttbar' in p:
	colors[p] = ROOT.kRed
    elif p == 'WJets':
	colors[p] = ROOT.kGreen
    elif p == 'ZJets':
	colors[p] = ROOT.kBlue
    elif p == 'QCD':
	colors[p] = ROOT.kYellow

varnames = {
    'mtop':'m_{top} [GeV]',
    'mtphi':'m_{t#phi} [GeV]',
    'mphi':'m_{#phi}',
    'deltaEta':'|#Delta #eta|'
}

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-y', type=str, dest='year',
                        action='store', required=True,
                        help='Year of set (16, 17, 18).')
    parser.add_argument('--logy',
                        action='store_true',
                        help='If flag passed, plot logarithmic distributions')
    parser.add_argument('--soverb',
                        action='store_true',
                        help='If flag passed, add a sub pad with signal/sqrt(background) calculation')
    args = parser.parse_args()

    histgroups = {}

    for sample in samples.keys():
	inFile = ROOT.TFile.Open('dijet_nano/NMinus1/NMinus1_{}_{}.root'.format(sample,args.year))
	histgroups[sample] = HistGroup(sample)
	for key in inFile.GetListOfKeys():
	    keyname = key.GetName()
	    varname = keyname
	    inhist = inFile.Get(key.GetName())
	    inhist.SetDirectory(0)
	    histgroups[sample].Add(varname,inhist)
	    print('Added {} distribution for sample {}'.format(varname, sample))
	inFile.Close()

    for varname in varnames.keys():
	plot_filename = 'plots/{}_{}{}{}.png'.format(varname, args.year,'_SoverB' if args.soverb else '', '_logy' if args.logy else '')
	bkg_hists, signal_hists = OrderedDict(), OrderedDict()
	for bkg in ['QCD','ttbar','WJets','ZJets']:
	    bkg_hists[bkg] = histgroups[bkg][varname]
	for sig in samples.keys():
	    if 'Tprime' not in sig: continue
	    signal_hists[sig] = histgroups[sig][varname]

	CompareShapes(
	    outfilename = plot_filename,
	    year = args.year,
	    prettyvarname = varnames[varname],
	    bkgs = bkg_hists,
	    signals = signal_hists,
	    colors = colors,
	    names = samples,
	    logy = args.logy,
	    doSoverB = args.soverb,
	    stackBkg = True
	)
	    

















