import ROOT, time
from collections import OrderedDict
from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp
ROOT.gROOT.SetBatch(True)

from THClass import THClass

def THselection(args):
    #ROOT.ROOT.EnableImplicitMT(args.threads)
    start = time.time()

    selection = THClass('dijet_nano/%s_%s_snapshot.txt'%(args.setname,args.era),args.era,1,1)
    selection.OpenForSelection(args.variation)
    selection.ApplyTrigs(args.trigEff)
    kinOnly = selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())

    out = ROOT.TFile.Open('THselection_%s%s_%s%s.root'%(args.setname,
                                                                  '' if args.topcut == '' else '_htag'+args.topcut.replace('.','p'),
                                                                  args.era,
                                                                  '' if args.variation == 'None' else '_'+args.variation),
                          'RECREATE')
    out.cd()
    #for t in ['deepTag','particleNet']:
    for t in ['particleNet']:
        if args.topcut != '':
            selection.cuts[t+'MD_HbbvsQCD'] = float(args.topcut)

        top_tagger = '%s_TvsQCD'%t
        higgs_tagger = '%sMD_HbbvsQCD'%t

        # Control region
        selection.a.SetActiveNode(kinOnly)
	# perform selection with CRv1 requirements
        #selection.ApplyTopPick(tagger=top_tagger,invert=False)
	# perform using CRv2 requirements
	selection.ApplyTopPick(tagger=top_tagger,invert=False,CRv2=higgs_tagger)
        passfailSR = selection.ApplyHiggsTag('CR', tagger=higgs_tagger)

        # Signal region
        selection.a.SetActiveNode(kinOnly)
        #selection.ApplyTopPick(tagger=top_tagger,invert=True)
	selection.ApplyTopPick(tagger=top_tagger,invert=True,CRv2=higgs_tagger)
        passfailCR = selection.ApplyHiggsTag('SR', tagger=higgs_tagger)

        for rkey,rpair in {"SR":passfailSR,"CR":passfailCR}.items():
            for pfkey,n in rpair.items():
                mod_name = "%s_%s_%s"%(t,rkey,pfkey)
                mod_title = "%s %s"%(rkey,pfkey)
                selection.a.SetActiveNode(n)
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
        selection.a.PrintNodeTree('NodeTree_selection.pdf',verbose=True)

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
    #args.threads = 1
    args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_{}.root'.format(args.era if 'APV' not in args.era else 16),'Pretag'], corrtype='weight')
    CompileCpp('THmodules.cc')
    THselection(args)
