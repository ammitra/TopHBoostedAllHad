import ROOT, time

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp
ROOT.gROOT.SetBatch(True)

from THClass import THClass

def main(args):
    ROOT.ROOT.EnableImplicitMT(args.threads)
    start = time.time()
    selection = THClass('dijet_nano/%s_%s_snapshot.txt'%(args.setname,args.era),int(args.era),1,1)
    # JME variations
    doStudies = False
    if args.variation.startswith('JE'):
        selection.a.Define('Dijet_pt_corr','hardware::HadamardProduct(Dijet_pt,Dijet_%s)'%args.variation)
        selection.a.Define('Dijet_msoftdrop_corr','hardware::HadamardProduct(Dijet_msoftdrop,Dijet_%s)'%args.variation)
    elif args.variation.startswith('JM'):
        selection.a.Define('Dijet_pt_corr','Dijet_pt')
        selection.a.Define('Dijet_msoftdrop_corr','hardware::HadamardProduct(Dijet_msoftdrop,Dijet_%s)'%args.variation)
    else:
        doStudies = True
        selection.a.Define('Dijet_pt_corr','Dijet_pt')
        selection.a.Define('Dijet_msoftdrop_corr','Dijet_msoftdrop')

    selection.a.Define('Dijet_vect','hardware::TLvector(Dijet_pt_corr, Dijet_eta, Dijet_phi, Dijet_msoftdrop_corr)')
    kinOnly = selection.ApplyStandardCorrections(snapshot=False)

    if doStudies:
        selection.a.Define('pt0','Dijet_pt_corr[0]')
        selection.a.Define('pt1','Dijet_pt_corr[1]')
        selection.a.Define('HT','pt0+pt1')
        selection.a.Define('deltaEta','abs(Dijet_eta[0] - Dijet_eta[1])')
        
        kinOnly = selection.a.Define('deltaY','abs(Dijet_vect[0].Rapidity() - Dijet_vect[1].Rapidity())')
        # Kinematic plots
        kinPlots = HistGroup('kinPlots')
        kinPlots.Add('pt0',selection.a.DataFrame.Histo1D(('pt0','Lead jet pt',100,350,2350),'pt0'))
        kinPlots.Add('pt1',selection.a.DataFrame.Histo1D(('pt1','Sublead jet pt',100,350,2350),'pt1'))
        kinPlots.Add('HT',selection.a.DataFrame.Histo1D(('HT','Sum of pt of two leading jets',150,700,3700),'HT'))
        kinPlots.Add('deltaEta',selection.a.DataFrame.Histo1D(('deltaEta','| #Delta #eta |',48,0,4.8),'deltaEta'))
        kinPlots.Add('deltaY',selection.a.DataFrame.Histo1D(('deltaY','| #Delta y |',60,0,3),'deltaY'))

    out = ROOT.TFile.Open('rootfiles/THselection_%s_%s%s.root'%(args.setname,args.era,'_'+args.variation if args.variation != '' else ''),'RECREATE')
    out.cd()
    for t in ['deepTagMD','particleNet']:
        selection.a.SetActiveNode(kinOnly)
        top_tagger = '%s_TvsQCD'%t
        higgs_tagger = '%s_HbbvsQCD'%t
        # Signal region
        # selection.DefineTopIdx(tagger=top_tagger,invert=False)
        selection.ApplyTopPick(tagger=top_tagger,invert=False)
        passfailSR = selection.ApplyHiggsTag(tagger=higgs_tagger)

        # Control region
        selection.a.SetActiveNode(kinOnly)
        # selection.DefineTopIdx(tagger=top_tagger,invert=True)
        selection.ApplyTopPick(tagger=top_tagger,invert=True)
        passfailCR = selection.ApplyHiggsTag(tagger=higgs_tagger)

        for rkey,rpair in {"SR":passfailSR,"CR":passfailCR}.items():
            for pfkey,n in rpair.items():
                mod_name = "%s_%s_%s"%(t,rkey,pfkey)
                mod_title = "%s %s"%(rkey,pfkey)
                selection.a.SetActiveNode(n)
                selection.a.MakeWeightCols()
                templates = selection.a.MakeTemplateHistos(ROOT.TH2F('MthvMh_%s'%mod_name,'MthvMh %s with %s'%(mod_title,t),40,60,260,28,800,2200),['Higgs_msoftdrop','mth'])
                templates.Do('Write')

    if doStudies: 
        kinPlots.Do('Write')
        selection.a.PrintNodeTree('NodeTree.pdf')
    print ('%s sec'%(time.time()-start))

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='era',
                        action='store', required=True,
                        help='Year of set (16, 17, 18).')
    parser.add_argument('-v', type=str, dest='variation',
                        action='store', default='',
                        help='JES_up, JES_down, JMR_up,...')
    args = parser.parse_args()
    args.threads = 1
    CompileCpp('THmodules.cc')
    main(args)
