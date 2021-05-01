import ROOT, time

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp
ROOT.gROOT.SetBatch(True)

from THClass import THClass

def main(args):
    ROOT.ROOT.EnableImplicitMT(args.threads)
    start = time.time()
    selection = THClass('dijet_nano/%s_%s_snapshot.txt'%(args.setname,args.era),int(args.era))
    selection.ApplyTrigs()
    # JME variations
    doStudies = selection.OpenForSelection(args.variation)
    kinOnly = selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())

    if doStudies:
        selection.a.Define('pt0','Dijet_pt_corr[0]')
        selection.a.Define('pt1','Dijet_pt_corr[1]')
        selection.a.Define('HT','pt0+pt1')
        selection.a.Define('deltaEta','abs(Dijet_eta[0] - Dijet_eta[1])')
        
        kinOnly = selection.a.Define('deltaY','abs(Dijet_vect[0].Rapidity() - Dijet_vect[1].Rapidity())')
        # Kinematic plots
        kinPlots = HistGroup('kinPlots')
        kinPlots.Add('pt0',selection.a.DataFrame.Histo1D(('pt0','Lead jet pt',100,350,2350),'pt0','weight__nominal'))
        kinPlots.Add('pt1',selection.a.DataFrame.Histo1D(('pt1','Sublead jet pt',100,350,2350),'pt1','weight__nominal'))
        kinPlots.Add('HT',selection.a.DataFrame.Histo1D(('HT','Sum of pt of two leading jets',150,700,3700),'HT','weight__nominal'))
        kinPlots.Add('deltaEta',selection.a.DataFrame.Histo1D(('deltaEta','| #Delta #eta |',48,0,4.8),'deltaEta','weight__nominal'))
        kinPlots.Add('deltaY',selection.a.DataFrame.Histo1D(('deltaY','| #Delta y |',60,0,3),'deltaY','weight__nominal'))

    if not selection.a.isData and doStudies:
        selection.ApplyTopPickViaMatch()
        kinPlots.Add('tIdx',selection.a.DataFrame.Histo1D(('tIdx','Top jet idx',2,0,2),'tIdx'))
        kinPlots.Add('hIdx',selection.a.DataFrame.Histo1D(('hIdx','Higgs jet idx',2,0,2),'hIdx'))
        
        selection.a.SetActiveNode(kinOnly)
        selection.a.ObjectFromCollection('LeadTop','Dijet',0)
        nminus1Node = selection.a.ObjectFromCollection('SubleadHiggs','Dijet',1)

    out = ROOT.TFile.Open('rootfiles/THselection_%s_%s%s.root'%(args.setname,args.era,'_'+args.variation if args.variation != 'None' else ''),'RECREATE')
    out.cd()
    for t in ['deepTag','particleNet']:
        top_tagger = '%s_TvsQCD'%t
        higgs_tagger = '%sMD_HbbvsQCD'%t

        # N-1
        if not selection.a.isData and doStudies:
            selection.a.SetActiveNode(nminus1Node)
            nminusGroup = selection.GetNminus1Group(t)
            nminusNodes = selection.a.Nminus1(nminusGroup)
            for n in nminusNodes.keys():
                if n.startswith('m'):
                    bins = [25,50,300]
                    if n.startswith('mH'): var = 'SubleadHiggs_msoftdrop_corr'
                    else: var = 'LeadTop_msoftdrop_corr'
                elif n == 'full': continue
                else:
                    bins = [20,0,1]
                    if n.endswith('H_cut'): var = 'SubleadHiggs_%s'%higgs_tagger
                    else: var = 'LeadTop_%s'%top_tagger
                print ('N-1: Plotting %s for node %s'%(var,n))
                kinPlots.Add(n+'_nminus1',nminusNodes[n].DataFrame.Histo1D((n+'_nminus1',n+'_nminus1',bins[0],bins[1],bins[2]),var,'weight__nominal'))

        # Signal region
        selection.a.SetActiveNode(kinOnly)
        selection.ApplyTopPick(tagger=top_tagger,invert=False)
        passfailSR = selection.ApplyHiggsTag(tagger=higgs_tagger)

        # Control region
        selection.a.SetActiveNode(kinOnly)
        selection.ApplyTopPick(tagger=top_tagger,invert=True)
        passfailCR = selection.ApplyHiggsTag(tagger=higgs_tagger)

        for rkey,rpair in {"SR":passfailSR,"CR":passfailCR}.items():
            for pfkey,n in rpair.items():
                mod_name = "%s_%s_%s"%(t,rkey,pfkey)
                mod_title = "%s %s"%(rkey,pfkey)
                selection.a.SetActiveNode(n)
                templates = selection.a.MakeTemplateHistos(ROOT.TH2F('MthvMh_%s'%mod_name,'MthvMh %s with %s'%(mod_title,t),40,60,260,28,800,2200),['Higgs_msoftdrop_corr','mth'])
                templates.Do('Write')

    if doStudies:
        kinPlots.Do('Write')
        selection.a.PrintNodeTree('NodeTree.pdf',verbose=True)
    if not selection.a.isData:
        scale = ROOT.TH1F('scale','xsec*lumi/genEventSumw',1,0,1)
        scale.SetBinContent(1,selection.GetXsecScale())
        scale.Write()
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
                        action='store', default='None',
                        help='JES_up, JES_down, JMR_up,...')
    args = parser.parse_args()
    args.threads = 1
    CompileCpp('THmodules.cc')
    main(args)
