import ROOT, time
from collections import OrderedDict
from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp
ROOT.gROOT.SetBatch(True)

from THClass import THClass

def getEfficiencies(analyzer, tagger, SRorCR, wp_loose, wp_tight):
    ''' 
	call this function after ApplyTopPick() has been called
	Therefore, we have to prepend the tagger with 'Higgs_'
    '''
    print('Obtaining efficiencies in {}'.format(SRorCR))
    tagger = 'Higgs_' + tagger
    start = analyzer.GetActiveNode()
    nTot = analyzer.DataFrame.Sum("genWeight").GetValue()
    print("nTot = {}".format(nTot))
    analyzer.Cut("Eff_L_cut","{0} > {1} && {0} < {2}".format(tagger, wp_loose, wp_tight))
    nL = analyzer.DataFrame.Sum("genWeight").GetValue()
    print("nL = {}".format(nL))
    analyzer.SetActiveNode(start)
    analyzer.Cut("Eff_T_cut","{0} > {1}".format(tagger, wp_tight))
    nT = analyzer.DataFrame.Sum("genWeight").GetValue()
    print("nT = {}".format(nT))
    effL = nL/nTot
    effT = nT/nTot
    analyzer.SetActiveNode(start)
    print('{}: effL = {}%'.format(SRorCR, effL*100.))
    print('{}: effT = {}%'.format(SRorCR, effT*100.))
    return effL, effT

def applyScaleFactors(analyzer, tagger, variation, SRorCR, eff_loose, eff_tight, wp_loose, wp_tight):
    '''
	creates PNetSFHandler object and creates the original and updated tagger categories
	must be called ONLY once, after calling ApplyTopPick() so proper Higgs vect is created
	Therefore, we have to prepend the tagger with 'Higgs_'
    '''
    print('Applying SFs in {}'.format(SRorCR))
    tagger = 'Higgs_' + tagger
    # instantiate Scale Factor class: {WPs}, {effs}, "year", variation
    CompileCpp('PNetSFHandler p_%s = PNetSFHandler({0.8,0.98}, {%f,%f}, "20%s", %i);'%(SRorCR, eff_loose, eff_tight, args.era, variation))
    # now create the column with original tagger category values (0: fail, 1: loose, 2: tight)
    analyzer.Define("OriginalTagCats","p_{}.createTag({})".format(SRorCR, tagger))
    # now create the column with *new* tagger categories, after applying logic. MUST feed in the original column (created in last step)
    analyzer.Define("NewTagCats","p_{}.updateTag(OriginalTagCats, Higgs_pt_corr, {})".format(SRorCR, tagger))

def THselection(args):
    ROOT.ROOT.EnableImplicitMT(args.threads)
    start = time.time()

    # check if signal
    signal = False
    if ('Tprime' in args.setname):
	signal = True
        # determine which variation to pass constructor
        if (args.variation == 'PNet_up'):
            var = 1
        elif (args.variation == 'PNet_down'):
            var = 2
        else:
            var = 0
        CompileCpp("ParticleNet_SF.cc")     # compile class for later use

    print('Opening dijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.era))
    selection = THClass('dijet_nano/%s_%s_snapshot.txt'%(args.setname,args.era),args.era,1,1)
    selection.OpenForSelection(args.variation)
    selection.ApplyTrigs(args.trigEff)
    kinOnly = selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())
    out = ROOT.TFile.Open('rootfiles/THselection_%s%s_%s%s.root'%(args.setname,
                                                                  '' if args.topcut == '' else '_htag'+args.topcut.replace('.','p'),
                                                                  args.era,
                                                                  '' if args.variation == 'None' else '_'+args.variation), 'RECREATE')
    out.cd()

    for t in ['particleNet']:	# add other taggers to this list if studying more than just ParticleNet
        if args.topcut != '':
            selection.cuts[t+'MD_HbbvsQCD'] = float(args.topcut)

        top_tagger = '%s_TvsQCD'%t
        higgs_tagger = '%sMD_HbbvsQCD'%t

        # Control region - INVERT TOP CUT
        selection.a.SetActiveNode(kinOnly)
	selection.ApplyTopPick(tagger=top_tagger,invert=True,CRv2=higgs_tagger)
	# now that top selection has been made for CR, we get the loose/tight efficiencies for the CR and make tagger categories (IF SIGNAL)
	if signal:
	    eff_L_CR, eff_T_CR = getEfficiencies(selection.a, higgs_tagger, 'CR', 0.8, 0.98)
	    applyScaleFactors(selection.a, higgs_tagger, var, 'CR', eff_L_CR, eff_T_CR, 0.8, 0.95)
        passfailCR = selection.ApplyHiggsTag('CR', tagger=higgs_tagger, signal=signal)

        # Signal region - KEEP TOP CUT
        selection.a.SetActiveNode(kinOnly)
	selection.ApplyTopPick(tagger=top_tagger,invert=False,CRv2=higgs_tagger)
        if signal:
            eff_L_SR, eff_T_SR = getEfficiencies(selection.a, higgs_tagger, 'SR', 0.8, 0.98)
            applyScaleFactors(selection.a, higgs_tagger, var, 'SR', eff_L_SR, eff_T_SR, 0.8, 0.95)
        passfailSR = selection.ApplyHiggsTag('SR', tagger=higgs_tagger, signal=signal)

	# rkey: SR/CR, pfkey: pass/loose/fail
        for rkey,rpair in {"SR":passfailSR,"CR":passfailCR}.items():
            for pfkey,n in rpair.items():
                mod_name = "%s_%s_%s"%(t,rkey,pfkey)
                mod_title = "%s %s"%(rkey,pfkey)
                selection.a.SetActiveNode(n)
		# MakeTemplateHistos takes in the template histogram and then the variables which to plot in the form [x, y]
		# in this case, 'Higgs_msoftdrop_corrH' is the x axis (phi mass) and 'mth' is the y axis (dijet mass)
		# both of these variables were created/defined during the ApplyTopPick() and ApplyHiggsTag() steps above (see THClass)
                templates = selection.a.MakeTemplateHistos(ROOT.TH2F('MthvMh_%s'%mod_name,'MthvMh %s with %s'%(mod_title,t),40,60,260,22,800,3000),['Higgs_msoftdrop_corrH','mth'])
                templates.Do('Write')

    # now process cutflow information
    cutflowInfo = OrderedDict([
	('nTop_CR',selection.nTop_CR), 
	('higgsF_CR',selection.higgsF_CR),
	('higgsL_CR',selection.higgsL_CR),
	('higgsP_CR',selection.higgsP_CR),
	('nTop_SR',selection.nTop_SR),
	('higgsF_SR',selection.higgsF_SR),
	('higgsL_SR',selection.higgsL_SR),
	('higgsP_SR',selection.higgsP_SR),
    ])

    nLabels = len(cutflowInfo)
    hCutflow = ROOT.TH1F('cutflow'.format(args.setname, args.era, args.variation), "Number of events after each cut", nLabels, 0.5, nLabels+0.5)
    nBin = 1
    for label, value in cutflowInfo.items():
	hCutflow.GetXaxis().SetBinLabel(nBin, label)
	hCutflow.AddBinContent(nBin, value)
	nBin += 1
    hCutflow.Write()

    if not selection.a.isData:
        scale = ROOT.TH1F('scale','xsec*lumi/genEventSumw',1,0,1)
        scale.SetBinContent(1,selection.GetXsecScale())
        scale.Write()
        #selection.a.PrintNodeTree('NodeTree_selection.pdf',verbose=True)

    print ('%s sec'%(time.time()-start))

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
    parser.add_argument('--topcut', type=str, dest='topcut',
                        action='store', default='',
                        help='Overrides config entry if non-empty')
    args = parser.parse_args()
    args.threads = 2

    # We must apply the 2017B triffer efficiency to ~12% of the 2017 MC
    # This trigEff correction is passed to ApplyTrigs() in the THselection() function
    if ('Data' not in args.setname) and (args.era == '17'): # we are dealing with MC from 2017
	cutoff = 0.11655	# fraction of total JetHT data belonging to 2017B
	TRand = ROOT.TRandom()
	rand = TRand.Uniform(0.0, 1.0)
	if rand < cutoff:	# apply the 2017B trigger efficiency to this MC 
	    print('Applying 2017B trigger efficiency')
	    args.trigEff = Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_17B.root','Pretag'],corrtype='weight')
	else:
	    args.trigEff = Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_17.root','Pretag'],corrtype='weight')
    else:
        args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_{}.root'.format(args.era if 'APV' not in args.era else 16),'Pretag'], corrtype='weight')

    CompileCpp('THmodules.cc')
    THselection(args)
