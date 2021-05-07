import ROOT, time

from TIMBER.Analyzer import HistGroup
from TIMBER.Tools.Common import CompileCpp
ROOT.gROOT.SetBatch(True)

from THClass import THClass

def main(args):
    ROOT.ROOT.EnableImplicitMT(args.threads)
    start = time.time()
    selection = THClass('dijet_nano/%s_%s_snapshot.txt'%(args.setname,args.era),int(args.era),1,1)
    selection.a.Define('Dijet_pt_corr','Dijet_pt')
    selection.a.Define('Dijet_msoftdrop_corr','Dijet_msoftdrop')
    kinOnly = selection.a.Define('Dijet_vect','hardware::TLvector(Dijet_pt_corr, Dijet_eta, Dijet_phi, Dijet_msoftdrop_corr)')
    
    # Kinematic plots
    jetPlots = HistGroup('jetPlots')
    # Taggers after mass selection
    selection.a.Define('TopMassBools','Dijet_msoftdrop_corr > 105 && Dijet_msoftdrop_corr < 210')
    selection.a.Define('DAK8TopScoresInMassWindow', 'Dijet_deepTag_TvsQCD[TopMassBools]')
    selection.a.Define('PNTopScoresInMassWindow', 'Dijet_particleNet_TvsQCD[TopMassBools]')
    jetPlots.Add('DAK8TopScoresInMassWindow',selection.a.DataFrame.Histo1D(('DAK8TopScoresInMassWindow','DeepAK8 top score for jets in top mass window',50,0,1),'DAK8TopScoresInMassWindow'))
    jetPlots.Add('PNTopScoresInMassWindow',selection.a.DataFrame.Histo1D(('PNTopScoresInMassWindow','ParticleNet top score for jets in top mass window',50,0,1),'PNTopScoresInMassWindow'))

    selection.a.Define('HiggsMassBools','Dijet_msoftdrop_corr > 100 && Dijet_msoftdrop_corr < 140')
    selection.a.Define('DAK8HiggsScoresInMassWindow','Dijet_deepTagMD_HbbvsQCD[HiggsMassBools]')
    selection.a.Define('PNHiggsScoresInMassWindow','Dijet_particleNet_HbbvsQCD[HiggsMassBools]')
    jetPlots.Add('DAK8HiggsScoresInMassWindow',selection.a.DataFrame.Histo1D(('DAK8HiggsScoresInMassWindow','DeepAK8 Higgs score for jets in Higgs mass window',50,0,1),'DAK8HiggsScoresInMassWindow'))
    jetPlots.Add('PNHiggsScoresInMassWindow',selection.a.DataFrame.Histo1D(('PNHiggsScoresInMassWindow','ParticleNet Higgs score for jets in Higgs mass window',50,0,1),'PNHiggsScoresInMassWindow'))

    # Mass after tagger selection
    selection.a.Define('TopDAK8Bools','Dijet_deepTag_TvsQCD > 0.9')
    selection.a.Define('TopPNBools','Dijet_particleNet_TvsQCD > 0.9')
    selection.a.Define('TopMassAfterDAK8Tag', 'Dijet_msoftdrop_corr[TopDAK8Bools]')
    selection.a.Define('TopMassAfterPNTag', 'Dijet_msoftdrop_corr[TopPNBools]')
    jetPlots.Add('TopMassAfterDAK8Tag',selection.a.DataFrame.Histo1D(('TopMassAfterDAK8Tag','Jet mass after DAK8 top score > 0.9',25,50,300),'TopMassAfterDAK8Tag'))
    jetPlots.Add('TopMassAfterPNTag',selection.a.DataFrame.Histo1D(('TopMassAfterPNTag','Jet mass after PN top score > 0.9',25,50,300),'TopMassAfterPNTag'))

    selection.a.Define('HiggsDAK8Bools','Dijet_deepTagMD_HbbvsQCD > 0.9')
    selection.a.Define('HiggsPNBools','Dijet_particleNet_HbbvsQCD > 0.9')
    selection.a.Define('HiggsMassAfterDAK8Tag', 'Dijet_msoftdrop_corr[HiggsDAK8Bools]')
    selection.a.Define('HiggsMassAfterPNTag', 'Dijet_msoftdrop_corr[HiggsPNBools]')
    jetPlots.Add('HiggsMassAfterDAK8Tag',selection.a.DataFrame.Histo1D(('HiggsMassAfterDAK8Tag','Jet mass after DAK8 Higgs score > 0.9',25,50,300),'HiggsMassAfterDAK8Tag'))
    jetPlots.Add('HiggsMassAfterPNTag',selection.a.DataFrame.Histo1D(('HiggsMassAfterPNTag','Jet mass after PN Higgs score > 0.9',25,50,300),'HiggsMassAfterPNTag'))

    selection.a.Define('GenPart_vect','hardware::TLvector(GenPart_pt, GenPart_eta, GenPart_phi, GenPart_mass)')

    out = ROOT.TFile.Open('rootfiles/THjetstudy_%s_%s%s.root'%(args.setname,args.era,'_'+args.variation if args.variation != '' else ''),'RECREATE')
    out.cd()
    presel = selection.a.GetActiveNode()
    # Assign jets on truth in parallel
    selection.a.SetActiveNode(presel)
    selection.ApplyTopPickViaMatch()
    truthtag = selection.a.Define('MassDiff','Top_msoftdrop_corr - Higgs_msoftdrop_corr')
    nicenames = {"deepTag":"DAK8^{top}", "particleNet":"PN^{top}"}
    for t in ['deepTag','particleNet']:
        selection.a.SetActiveNode(presel)
        top_tagger = '%s_TvsQCD'%t
        # higgs_tagger = '%s_HbbvsQCD'%t
        # Signal region
        selection.ApplyTopPick(tagger=top_tagger,invert=False)

        selection.a.Define('MassDiff','Top_msoftdrop_corr - Higgs_msoftdrop_corr')
        selection.a.Define('NNDiff','Top_{0} - Higgs_{0}'.format(top_tagger))
        jetPlots.Add('MassDiffvsNNDiff_%s'%t,
                        selection.a.DataFrame.Histo2D(
                            ('MassDiffvsNNDiff_%s'%t,'(m_{{t}} - m_{{H}}) vs ({0}_{{t}} - {0}_{{H}})'.format(nicenames[t]),25,-100,150,40,-1,1),
                            'MassDiff','NNDiff'
                        )
                    )
        # Look at unmatched pieces
        checkpoint = selection.a.GetActiveNode()
        selection.a.Cut('NotGenMatchTop','!MatchToGen(6, Top_vect, GenPart_vect, GenPart_pdgId)')
        selection.a.Cut('NotGenMatchH','!MatchToGen(25, Higgs_vect, GenPart_vect, GenPart_pdgId)')
        jetPlots.Add('MassDiffvsNNDiff_%s_BadMatch'%t,
                        selection.a.DataFrame.Histo2D(
                            ('MassDiffvsNNDiff_%s_BadMatch'%t,'(m_{{t}} - m_{{H}}) vs ({0}_{{t}} - {0}_{{H}}) - Bad matches'.format(nicenames[t]),25,-100,150,40,-1,1),
                            'MassDiff','NNDiff'
                        )
                    )
        # Look at matched pieces
        selection.a.SetActiveNode(checkpoint)
        selection.a.Cut('GenMatchTop','MatchToGen(6, Top_vect, GenPart_vect, GenPart_pdgId)')
        selection.a.Cut('GenMatchH','MatchToGen(25, Higgs_vect, GenPart_vect, GenPart_pdgId)')
        jetPlots.Add('MassDiffvsNNDiff_%s_GoodMatch'%t,
                        selection.a.DataFrame.Histo2D(
                            ('MassDiffvsNNDiff_%s_GoodMatch'%t,'(m_{{t}} - m_{{H}}) vs ({0}_{{t}} - {0}_{{H}}) - Good matches'.format(nicenames[t]),25,-100,150,40,-1,1),
                            'MassDiff','NNDiff'
                        )
                    )
        # Assign jets on truth
        selection.a.SetActiveNode(truthtag)
        selection.a.Define('NNDiff_%s'%t,'Top_{0} - Higgs_{0}'.format(top_tagger))
        jetPlots.Add('MassDiffvsNNDiff_%s_TruthMatch'%t,
                        selection.a.DataFrame.Histo2D(
                            ('MassDiffvsNNDiff_%s_TruthMatch'%t,'(m_{{t}} - m_{{H}}) vs ({0}_{{t}} - {0}_{{H}}) - Truth matches'.format(nicenames[t]),25,-100,150,40,-1,1),
                            'MassDiff','NNDiff_%s'%t
                        )
                    )

    jetPlots.Do('Write')
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
                        action='store', default='None',
                        help='JES_up, JES_down, JMR_up,...')
    args = parser.parse_args()
    args.threads = 4
    CompileCpp('THmodules.cc')
    main(args)
