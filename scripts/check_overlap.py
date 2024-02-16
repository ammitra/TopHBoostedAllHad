'''
Script to compare the overlap of events in the ttbar CR and the SR. 
This is done by running through the selection process up until the cuts to form the various regions:

1. Identify top candidate jet (with SFs, etc if signal)
2. Make columns of the PNet and DeepAK8 scores of the top candidate and "Higgs" candidate jet

The results will be plotted by the script `scripts/check_ttbarCR_SR_orthogonality.py`
'''

import ROOT, time
from collections import OrderedDict
from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp
ROOT.gROOT.SetBatch(True)

from THClass import THClass

def getXbbEfficiencies(analyzer, tagger, SRorCR, wp_loose, wp_tight):
    ''' 
	call this function after ApplyTopPick() has been called
	Therefore, we have to prepend the tagger with 'Higgs_'
    '''
    print('Obtaining efficiencies in {}'.format(SRorCR))
    tagger = 'Higgs_' + tagger
    start = analyzer.GetActiveNode()
    nTot = analyzer.DataFrame.Sum("genWeight").GetValue()
    print("nTot = {}".format(nTot))
    analyzer.Cut("Eff_L_{}_cut".format(SRorCR),"{0} > {1} && {0} < {2}".format(tagger, wp_loose, wp_tight))
    nL = analyzer.DataFrame.Sum("genWeight").GetValue()
    print("nL = {}".format(nL))
    analyzer.SetActiveNode(start)
    analyzer.Cut("Eff_T_{}_cut".format(SRorCR),"{0} > {1}".format(tagger, wp_tight))
    nT = analyzer.DataFrame.Sum("genWeight").GetValue()
    print("nT = {}".format(nT))
    effL = nL/nTot
    effT = nT/nTot
    analyzer.SetActiveNode(start)
    print('{}: effL = {}%'.format(SRorCR, effL*100.))
    print('{}: effT = {}%'.format(SRorCR, effT*100.))
    return effL, effT

def getTopEfficiencies(analyzer, tagger, wp, idx, tag):
    print('Obtaining efficiencies for jet at idx {}'.format(idx))
    start = analyzer.GetActiveNode()
    nTot = analyzer.DataFrame.Sum("genWeight").GetValue()
    print("nTot = {}".format(nTot))
    analyzer.Cut("Eff_jet{}_{}_cut".format(idx, tag),"{} > {}".format(tagger, wp))
    nT = analyzer.DataFrame.Sum("genWeight").GetValue()
    print('nT = {}'.format(nT))
    eff = nT/nTot
    print('SR: eff = {}'.format(eff*100.))
    analyzer.SetActiveNode(start)
    return eff

def applyScaleFactors(analyzer, tagger, variation, SRorCR, eff_loose, eff_tight, wp_loose, wp_tight):
    '''
	creates PNetSFHandler object and creates the original and updated tagger categories
	must be called ONLY once, after calling ApplyTopPick() so proper Higgs vect is created
	Therefore, we have to prepend the tagger with 'Higgs_'
    '''
    print('Applying SFs in {}'.format(SRorCR))
    tagger = 'Higgs_' + tagger
    # instantiate Scale Factor class: {WPs}, {effs}, "year", variation
    CompileCpp('PNetXbbSFHandler p_%s = PNetXbbSFHandler({0.8,0.98}, {%f,%f}, "20%s", %i);'%(SRorCR, eff_loose, eff_tight, args.era, variation))
    # now create the column with original tagger category values (0: fail, 1: loose, 2: tight)
    analyzer.Define("OriginalTagCats","p_{}.createTag({})".format(SRorCR, tagger))
    # now create the column with *new* tagger categories, after applying logic. MUST feed in the original column (created in last step)
    analyzer.Define("NewTagCats","p_{}.updateTag(OriginalTagCats, Higgs_pt_corr, {})".format(SRorCR, tagger))

def THselection(args):
    assert(args.variation == 'None')
    ROOT.ROOT.EnableImplicitMT(args.threads)
    start = time.time()
    signal = False

    print('Opening dijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.era))
    selection = THClass('dijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.era),args.era,1,1)
    selection.OpenForSelection(args.variation)

    # apply HT cut due to improved trigger effs
    selection.a.Cut('HT_cut','HT > {}'.format(args.HT))

    selection.ApplyTrigs(args.trigEff)

    # scale factor application
    if ('Tprime' in args.setname):
	signal = True
	TopVar = 0
	XbbVar = 0

    top_tagger   = 'particleNet_TvsQCD' 	# PNet top tagger
    higgs_tagger = 'particleNetMD_HbbvsQCD'	# PNet Xbb tagger

    kinOnly = selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())

    # perform the top, Higgs identification
    if signal:
	selection.a.SetActiveNode(kinOnly)
	# first perform top ID
	e0SR = getTopEfficiencies(analyzer=selection.a, tagger='Dijet_'+top_tagger+'[0]', wp=0.94, idx=0, tag='sr1')
	e1SR = getTopEfficiencies(analyzer=selection.a, tagger='Dijet_'+top_tagger+'[1]', wp=0.94, idx=1, tag='sr2')
	selection.ApplyTopPick_Signal(TopTagger='Dijet_'+top_tagger, XbbTagger='Dijet_'+higgs_tagger, pt='Dijet_pt_corr', mass='Dijet_msoftdrop_corrT', TopScoreCut=0.94, eff0=e0SR, eff1=e1SR, year=args.era, TopVariation=TopVar, invert=False, ttbarCR=True)
	# now perform Higgs SF application + ID
	eff_L_ttbarCR, eff_T_ttbarCR = getXbbEfficiencies(selection.a, higgs_tagger, 'ttbarCR', 0.8, 0.98)
	applyScaleFactors(selection.a, higgs_tagger, XbbVar, 'ttbarCR', eff_L_ttbarCR, eff_T_ttbarCR, 0.8, 0.95)
	
    else:
	selection.a.SetActiveNode(kinOnly)
	selection.ApplyTopPick(tagger=top_tagger,invert=False,CRv2=higgs_tagger,ttbarCR=True)

    # Save out the scale so we know how many events to plot for each
    scale = selection.GetXsecScale()
    selection.a.Define('xsec_scale',str(scale))

    # now choose the columns to save - PNet/DeepAK8 scores of the phi candidate jet
    cols = [
        'Higgs_deepTagMD_TvsQCD',	# DeepAK8MD top tag score on Higgs jet
        'Higgs_particleNetMD_HbbvsQCD', # PNet Xbb score on Higgs jet
	'xsec_scale' 			# xsec*lumi/genEventSumW
    ]
    # Fail/Loose/Tight Higgs tag after SF applications (just so we can compare which jets actually pass)
    if signal: cols.append('NewTagCats')

    # save it all out to a new rootfile
    selection.a.Snapshot(
	cols, 
	'rootfiles/ttbarCR_vs_SR_overlap_HT{}_{}_{}.root'.format(args.HT,args.setname,args.era),
	'Events',openOption='RECREATE',saveRunChain=False
    )


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='era',
                        action='store', required=True,
                        help='Year of set (16, 16APV, 17, 18).')
    parser.add_argument('-v', type=str, dest='variation',
                        action='store', default='None',
                        help='JES_up, JES_down, JMR_up,...')
    parser.add_argument('--HT', type=str, dest='HT',
                        action='store', default='0',
                        help='Value of HT to cut on')
    parser.add_argument('--topcut', type=str, dest='topcut',
                        action='store', default='',
                        help='Overrides config entry if non-empty')
    args = parser.parse_args()
    args.threads = 2

    # Updated method using the trigger efficiencies parameterized by 2D function
    if ('Data' not in args.setname) and (args.era == '17'): # we are dealing with MC from 2017
        cutoff = 0.11655        # fraction of total JetHT data belonging to 2017B
        TRand = ROOT.TRandom()
        rand = TRand.Uniform(0.0, 1.0)
        if rand < cutoff:       # apply the 2017B trigger efficiency to this MC
            print('Applying 2017B trigger efficiency')
            args.trigEff = Correction("TriggerEff17",'EffLoader_2DfittedHist.cc',['out_Eff_2017B.root','Eff_2017B'],corrtype='weight')
        else:
            args.trigEff = Correction("TriggerEff17",'EffLoader_2DfittedHist.cc',['out_Eff_2017.root','Eff_2017'],corrtype='weight')
    else:
	if args.era == '16APV': era = '16'
	else: era = args.era
        args.trigEff = Correction("TriggerEff%s"%era,'EffLoader_2DfittedHist.cc',['out_Eff_20%s.root'%era,'Eff_20%s'%era],corrtype='weight')

    CompileCpp('THmodules.cc')
    if ('Tprime' in args.setname):
	#CompileCpp('ParticleNet_TopSF.cc')
	CompileCpp('ParticleNet_XbbSF.cc')
    THselection(args)
