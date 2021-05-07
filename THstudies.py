import ROOT, time

from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp
ROOT.gROOT.SetBatch(True)

from THClass import THClass

# Not for use with data
def THstudies(args):
    print ('PROCESSING: %s %s'%(args.setname, args.era))
    ROOT.ROOT.EnableImplicitMT(args.threads)
    start = time.time()
    # Base setup
    selection = THClass('dijet_nano/%s_%s_snapshot.txt'%(args.setname,args.era),int(args.era),1,1)
    selection.OpenForSelection('None')
    selection.a.Define('Dijet_vect','hardware::TLvector(Dijet_pt_corr, Dijet_eta, Dijet_phi, Dijet_msoftdrop_corrT)')
    selection.a.Define('mth','hardware::InvariantMass(Dijet_vect)')
    selection.a.Define('m_avg','(Dijet_msoftdrop_corrT[0]+Dijet_msoftdrop_corrT[1])/2') # Use the top version of the corrected mass
                                                                                        # since it still has JES/JER which both would get anyway
    selection.ApplyTrigs(args.trigEff)
    selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())
    
    # Kinematic definitions
    selection.a.Define('pt0','Dijet_pt_corr[0]')
    selection.a.Define('pt1','Dijet_pt_corr[1]')
    selection.a.Define('HT','pt0+pt1')
    selection.a.Define('deltaEta','abs(Dijet_eta[0] - Dijet_eta[1])')
    selection.a.Define('deltaPhi','hardware::DeltaPhi(Dijet_phi[0],Dijet_phi[1])')
    kinOnly = selection.a.Define('deltaY','abs(Dijet_vect[0].Rapidity() - Dijet_vect[1].Rapidity())')
    
    # Kinematic plots
    kinPlots = HistGroup('kinPlots')
    kinPlots.Add('pt0',selection.a.DataFrame.Histo1D(('pt0','Lead jet pt',100,350,2350),'pt0','weight__nominal'))
    kinPlots.Add('pt1',selection.a.DataFrame.Histo1D(('pt1','Sublead jet pt',100,350,2350),'pt1','weight__nominal'))
    kinPlots.Add('HT',selection.a.DataFrame.Histo1D(('HT','Sum of pt of two leading jets',150,700,3700),'HT','weight__nominal'))
    kinPlots.Add('deltaEta',selection.a.DataFrame.Histo1D(('deltaEta','| #Delta #eta |',48,0,4.8),'deltaEta','weight__nominal'))
    kinPlots.Add('deltaPhi',selection.a.DataFrame.Histo1D(('deltaPhi','| #Delta #phi |',32,1,3.14),'deltaPhi','weight__nominal'))
    kinPlots.Add('deltaY',selection.a.DataFrame.Histo1D(('deltaY','| #Delta y |',60,0,3),'deltaY','weight__nominal'))

    # Check MC truth to get jet idx assignment
    selection.ApplyTopPickViaMatch()
    kinPlots.Add('tIdx_true',selection.a.DataFrame.Histo1D(('tIdx_true','Top jet idx based on MC truth',2,0,2),'tIdx'))
    kinPlots.Add('hIdx_true',selection.a.DataFrame.Histo1D(('hIdx_true','Higgs jet idx based on MC truth',2,0,2),'hIdx'))
    
    # Do N-1 setup before splitting into DAK8 and PN - assume leading top
    #    This is a 50/50 assumption that kills the stats by 50% but
    #    it allows us to make the plots with real world possibility that
    #    there's Higgs and top cross contamination. Also helps to do this without
    #    too much hastle.
    selection.a.SetActiveNode(kinOnly)
    selection.a.ObjectFromCollection('LeadTop','Dijet',0)
    nminus1Node = selection.a.ObjectFromCollection('SubleadHiggs','Dijet',1)

    out = ROOT.TFile.Open('rootfiles/THstudies_%s_%s%s.root'%(args.setname,args.era,'_'+args.variation if args.variation != 'None' else ''),'RECREATE')
    out.cd()
    for t in ['deepTag','particleNet']:
        top_tagger = '%s_TvsQCD'%t
        higgs_tagger = '%sMD_HbbvsQCD'%t

        # N-1
        selection.a.SetActiveNode(nminus1Node)
        nminusGroup = selection.GetNminus1Group(t)
        nminusNodes = selection.a.Nminus1(nminusGroup)
        for n in nminusNodes.keys():
            if n.startswith('m'):
                bins = [25,50,300]
                if n.startswith('mH'): var = 'SubleadHiggs_msoftdrop_corrH'
                else: var = 'LeadTop_msoftdrop_corrT'
            elif n == 'full': continue
            else:
                bins = [50,0,1]
                if n.endswith('H_cut'): var = 'SubleadHiggs_%s'%higgs_tagger
                else: var = 'LeadTop_%s'%top_tagger
            print ('N-1: Plotting %s for node %s'%(var,n))
            kinPlots.Add(n+'_nminus1',nminusNodes[n].DataFrame.Histo1D((n+'_nminus1',n+'_nminus1',bins[0],bins[1],bins[2]),var,'weight__nominal'))

    kinPlots.Do('Write')
    selection.a.PrintNodeTree('NodeTree.pdf',verbose=True)
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
    args.threads = 8
    args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_%s.root'%args.era,'Pretag'], corrtype='weight')
    CompileCpp('THmodules.cc')
    THstudies(args)
