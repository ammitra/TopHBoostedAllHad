############################################################################
# script for plotting the HT vs sum of jet0,jet1 pT
# currently useless, since snapshots only save dijet collection,
# and not FatJet which would include all FatJets in the evnt from 
# which to determine HT. As it is currently, realHT == PTSum
# since Sum(Dijet_pt_corr) = (Dijet_pt_corr[0]+Dijet_pt_corr[1])
#
# Instead, check the HT==(pt0+pt1) vs invariant mass 
############################################################################
import ROOT, time
from collections import OrderedDict
from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp
ROOT.gROOT.SetBatch(True)

# some scripts for doing the selection
from THselection import *

from THClass import THClass

def applyScaleFactors_local(analyzer, tagger, variation, SRorCR, eff_loose, eff_tight, wp_loose, wp_tight):
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

def check(args):
    ROOT.ROOT.EnableImplicitMT(2)

    print('Opening dijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.era))
    selection = THClass('dijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.era),args.era,1,1)
    selection.OpenForSelection('None')

    # apply HT cut due to improved trigger effs
    before = selection.a.DataFrame.Count()
    selection.a.Cut('HT_cut','HT > {}'.format(args.HT))
    after = selection.a.DataFrame.Count()

    selection.ApplyTrigs(args.trigEff)

    signal=False
    if 'Tprime' in args.setname:
	signal=True
	TopVar = XbbVar = 0 #nominal

    kinOnly = selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())

    for t in ['particleNet']:   # add other taggers to this list if studying more than just ParticleNet
        top_tagger = '%s_TvsQCD'%t
        higgs_tagger = '%sMD_HbbvsQCD'%t

        # SIGNAL
        if signal:
            # CONTROL REGION - INVERT TOP CUT
            print("CONTROL REGION --------------------------------------------------------------------------------------------------------")
            selection.a.SetActiveNode(kinOnly)
            e0CR = getTopEfficiencies(analyzer=selection.a, tagger='Dijet_'+top_tagger+'[0]', wp=0.94, idx=0, tag='cr1')
            e1CR = getTopEfficiencies(analyzer=selection.a, tagger='Dijet_'+top_tagger+'[1]', wp=0.94, idx=1, tag='cr2')
            selection.ApplyTopPick_Signal(TopTagger='Dijet_'+top_tagger, XbbTagger='Dijet_'+higgs_tagger, pt='Dijet_pt_corr', TopScoreCut=0.94, eff0=e0CR, eff1=e1CR, year=args.era, TopVariation=TopVar, invert=True)
            eff_L_CR, eff_T_CR = getXbbEfficiencies(selection.a, higgs_tagger, 'CR', 0.8, 0.98)
            applyScaleFactors_local(selection.a, higgs_tagger, XbbVar, 'CR', eff_L_CR, eff_T_CR, 0.8, 0.95)
            passfailCR = selection.ApplyHiggsTag('CR', tagger=higgs_tagger, signal=signal)

        # EVERYTHING ELSE
        else:
            # CONTROL REGION - INVERT TOP CUT
            selection.a.SetActiveNode(kinOnly)
            selection.ApplyTopPick(tagger=top_tagger,invert=True,CRv2=higgs_tagger)            
	    passfailCR = selection.ApplyHiggsTag('CR', tagger=higgs_tagger, signal=signal)

	c = ROOT.TCanvas('c','c')
	c.cd()
	c.Print('plots/HTvsMass_{}_HT{}.pdf['.format(args.setname+'_'+args.era, args.HT))
	# rkey: SR/CR, pfkey: pass/loose/fail
        for rkey,rpair in {"CR":passfailCR}.items():
            for pfkey,n in rpair.items():
		selection.a.SetActiveNode(n)
		region = '{}_{}'.format(rkey,pfkey)
		h1 = selection.a.GetActiveNode().DataFrame.Histo2D(('name','(p_{T}^{jet1}+p_{T}^{jet2}) vs m_{t\phi} %s'%(region),30,0,3000,30,0,3000),'HT','mth')
		h1.GetXaxis().SetTitle('(p_{T}^{jet1}+p_{T}^{jet2})')
		h1.GetYaxis().SetTitle('m_{t\phi}')
		#selection.a.Define('TopPlusPhi_pt_{}'.format(region),'Top_pt_corr+Higgs_pt_corr')
		#h2 = selection.a.GetActiveNode().DataFrame.Histo2D(('name','(p_{T}^{top}+p_{T}^{\phi}) vs m_{t\phi} %s'%(region),30,0,3000,30,0,3000),'TopPlusPhi_pt_{}'.format(region),'mth')
		#h2.GetXaxis().SetTitle('(p_{T}^{top}+p_{T}^{\phi})')
		#h2.GetYaxis().SetTitle('m_{t\phi}')
		c.Clear()
		h1.Draw('colz')
		c.Print('plots/HTvsMass_{}_HT{}.pdf'.format(args.setname+'_'+args.era, args.HT))
		c.Clear()
		#h2.Draw('colz')
		#c.Print('plots/HTvsMass_{}_HT{}.pdf'.format(args.setname, args.HT))
		#c.Clear()
	c.Print('plots/HTvsMass_{}_HT{}.pdf]'.format(args.setname+'_'+args.era, args.HT))

    '''
    hist1 = selection.a.GetActiveNode().DataFrame.Histo2D(('name','(p_{T}^{jet1}+p_{T}^{jet2}) vs m_{t\phi}',30,0,3000,30,0,3000),'HT','mth')
    hist1.GetXaxis().SetTitle('p_{T}^{jet1}+p_{T}^{jet2}')
    hist1.GetYaxis().SetTitle('m_{t\phi}')
    selection.a.Define('TopPlusPhi_pt','Top_pt_corr+Higgs_pt_corr')
    hist2 = selection.a.GetActiveNode().DataFrame.Histo2D(('name','(p_{T}^{top}+p_{T}^{\phi}) vs m_{t\phi}',30,0,3000,30,0,3000),'TopPlusPhi_pt','mth')
    hist2.GetXaxis().SetTitle('p_{T}^{top}+p_{T}^{phi}')
    hist2.GetYaxis().SetTitle('m_{t\phi}')

    c = ROOT.TCanvas('c','c')
    c.cd()
    c.Print('plots/HTvsMass_{}_HT{}.pdf['.format(args.setname, args.HT))
    c.Clear()
    hist1.Draw('colz')
    c.Print('plots/HTvsMass_{}_HT{}.pdf'.format(args.setname, args.HT))
    c.Clear()
    hist2.Draw('colz')
    c.Print('plots/HTvsMass_{}_HT{}.pdf'.format(args.setname,args.HT))
    c.Clear()
    c.Print('plots/HTvsMass_{}_HT{}.pdf]'.format(args.setname, args.HT))
    '''

if __name__=='__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='era',
                        action='store', required=True,
                        help='Year of set (16, 16APV, 17, 18).')
    parser.add_argument('--HT', type=str, dest='HT',
                        action='store', required=True,
                        help='HT cut applied')
    args = parser.parse_args()

    if ('Data' not in args.setname) and (args.era == '17'): # we are dealing with MC from 2017
        cutoff = 0.11655        # fraction of total JetHT data belonging to 2017B
        TRand = ROOT.TRandom()
        rand = TRand.Uniform(0.0, 1.0)
        if rand < cutoff:       # apply the 2017B trigger efficiency to this MC
            print('Applying 2017B trigger efficiency')
            args.trigEff = Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_HT{}_17B.root'.format(args.HT),'Pretag'],corrtype='weight')
        else:
            args.trigEff = Correction("TriggerEff17",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_HT{}_17.root'.format(args.HT),'Pretag'],corrtype='weight')
    else:
        args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_HT{}_{}.root'.format(args.HT,args.era if 'APV' not in args.era else 16),'Pretag'], corrtype='weight')

    CompileCpp('THmodules.cc')
    if ('Tprime' in args.setname):
        CompileCpp('ParticleNet_XbbSF.cc')

    check(args)
