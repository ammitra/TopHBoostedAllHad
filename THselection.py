import ROOT, time

from TIMBER.Analyzer import HistGroup
ROOT.gROOT.SetBatch(True)

from THClass import THClass

def main(args):
    ROOT.ROOT.EnableImplicitMT(args.threads)
    start = time.time()
    selection = THClass('dijet_nano/%s_%s_snapshot.txt'%(args.setname,args.era),int(args.era),1,1)
    selection.a.Define('pt0','Dijet_pt[0]')
    selection.a.Define('pt1','Dijet_pt[1]')
    selection.a.Define('HT','ROOT::VecOps::Sum(Dijet_pt)')
    selection.a.Define('deltaEta','abs(Dijet_eta[0] - Dijet_eta[1])')
    selection.a.Define('Dijet_vect','hardware::TLvector(Dijet_pt, Dijet_eta, Dijet_phi, Dijet_msoftdrop)')
    selection.a.Define('deltaY','abs(Dijet_vect[0].Rapidity() - Dijet_vect[1].Rapidity())')
    kinOnly = selection.ApplyStandardCorrections(snapshot=False)

    # Kinematic plots
    kinPlots = HistGroup('kinPlots')
    kinPlots.Add('pt0',selection.a.DataFrame.Histo1D(('pt0','Lead jet pt',100,350,2350),'pt0'))
    kinPlots.Add('pt1',selection.a.DataFrame.Histo1D(('pt1','Sublead jet pt',100,350,2350),'pt1'))
    kinPlots.Add('HT',selection.a.DataFrame.Histo1D(('HT','Sum of pt of two leading jets',150,700,3700),'HT'))
    kinPlots.Add('deltaEta',selection.a.DataFrame.Histo1D(('deltaEta','| #Delta #eta |',48,0,4.8),'deltaEta'))
    kinPlots.Add('deltaY',selection.a.DataFrame.Histo1D(('deltaY','| #Delta y |',60,0,3),'deltaY'))

    # Taggers after mass selection
    selection.a.Define('TopMassBools','Dijet_msoftdrop > 105 && Dijet_msoftdrop < 210')
    selection.a.Define('DAK8TopScoresInMassWindow', 'Dijet_deepTagMD_TvsQCD[TopMassBools]')
    selection.a.Define('PNTopScoresInMassWindow', 'Dijet_particleNet_TvsQCD[TopMassBools]')
    kinPlots.Add('DAK8TopScoresInMassWindow',selection.a.DataFrame.Histo1D(('DAK8TopScoresInMassWindow','DeepAK8 top score for jets in mass window',50,0,1),'DAK8TopScoresInMassWindow'))
    kinPlots.Add('PNTopScoresInMassWindow',selection.a.DataFrame.Histo1D(('PNTopScoresInMassWindow','ParticleNet top score for jets in mass window',50,0,1),'PNTopScoresInMassWindow'))

    selection.a.Define('HiggsMassBools','Dijet_msoftdrop > 100 && Dijet_msoftdrop < 140')
    selection.a.Define('DAK8HiggsScoresInMassWindow','Dijet_deepTagMD_HbbvsQCD[HiggsMassBools]')
    selection.a.Define('PNHiggsScoresInMassWindow','Dijet_particleNet_HbbvsQCD[HiggsMassBools]')
    kinPlots.Add('DAK8HiggsScoresInMassWindow',selection.a.DataFrame.Histo1D(('DAK8HiggsScoresInMassWindow','DeepAK8 Higgs score for jets in mass window',50,0,1),'DAK8HiggsScoresInMassWindow'))
    kinPlots.Add('PNHiggsScoresInMassWindow',selection.a.DataFrame.Histo1D(('PNHiggsScoresInMassWindow','ParticleNet Higgs score for jets in mass window',50,0,1),'PNHiggsScoresInMassWindow'))

    # Mass after tagger selection
    selection.a.Define('TopDAK8Bools','Dijet_deepTagMD_TvsQCD > 0.6')
    selection.a.Define('TopPNBools','Dijet_particleNet_TvsQCD > 0.6')

    selection.a.Define('TopMassAfterDAK8Tag', 'Dijet_msoftdrop[TopDAK8Bools]')
    selection.a.Define('TopMassAfterPNTag', 'Dijet_msoftdrop[TopPNBools]')
    kinPlots.Add('TopMassAfterDAK8Tag',selection.a.DataFrame.Histo1D(('TopMassAfterDAK8Tag','Jet mass after DAK8 score > 0.6',25,50,300),'TopMassAfterDAK8Tag'))
    kinPlots.Add('TopMassAfterPNTag',selection.a.DataFrame.Histo1D(('TopMassAfterPNTag','Jet mass after PN score > 0.6',25,50,300),'TopMassAfterPNTag'))

    selection.a.Define('HiggsDAK8Bools','Dijet_deepTagMD_HbbvsQCD > 0.6')
    selection.a.Define('HiggsPNBools','Dijet_particleNet_HbbvsQCD > 0.6')

    selection.a.Define('HiggsMassAfterDAK8Tag', 'Dijet_msoftdrop[HiggsDAK8Bools]')
    selection.a.Define('HiggsMassAfterPNTag', 'Dijet_msoftdrop[HiggsPNBools]')
    kinPlots.Add('HiggsMassAfterDAK8Tag',selection.a.DataFrame.Histo1D(('HiggsMassAfterDAK8Tag','Jet mass after DAK8 score > 0.6',25,50,300),'HiggsMassAfterDAK8Tag'))
    kinPlots.Add('HiggsMassAfterPNTag',selection.a.DataFrame.Histo1D(('HiggsMassAfterPNTag','Jet mass after PN score > 0.6',25,50,300),'HiggsMassAfterPNTag'))

    out = ROOT.TFile.Open('rootfiles/THselection_%s_%s.root'%(args.setname,args.era),'RECREATE')
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

        for n in passfailSR.values()+passfailCR.values():
            selection.a.SetActiveNode(n)
            selection.a.MakeWeightCols()
            templates = selection.a.MakeTemplateHistos(ROOT.TH2F('MthvMh_%s'%t,'MthvMh with %s'%t,40,60,260,28,800,2200),['Higgs_msoftdrop','mth'])
            templates.Do('Write')

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
    args = parser.parse_args()
    args.threads = 1
    main(args)
