import ROOT, time
from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp, ExecuteCmd
from TIMBER.Tools.Plot import CompareShapes, EasyPlots
ROOT.gROOT.SetBatch(True)

from THClass import THClass

def leadMass(args):
    print('PROCESSING: {} {}'.format(args.setname, args.era))
    ROOT.ROOT.EnableImplicitMT(args.threads)
    start = time.time()
    # base setup
    selection = THClass('dijet_nano/{}_{}_snapshot.txt'.format(args.setname, args.era),int(args.era),1,1)
    selection.OpenForSelection('None')
    selection.a.Define('Dijet_vect','hardware::TLvector(Dijet_pt_corr, Dijet_eta, Dijet_phi, Dijet_msoftdrop_corrT)')
    selection.a.Define('mth','hardware::InvariantMass(Dijet_vect)')
    selection.a.Define('m_avg','(Dijet_msoftdrop_corrT[0]+Dijet_msoftdrop_corrT[1])/2')
    selection.ApplyTrigs(args.trigEff)
    # come back to this node for each of the three plots of interest
    baseNode = selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())

    out = ROOT.TFile.Open('rootfiles/leadMassStudies_{}_{}.root'.format(args.setname,args.era),'RECREATE')
    out.cd()

    # now we are interested in the leading jet mass after:
    #	1) immediately after preselection (snapshot)
    massPlots = HistGroup('massPlots')
    selection.a.Define('m0_nominal','Dijet_msoftdrop_corrT[0]')	    # leading jet mass after snapshot phase (nominal)
    massPlots.Add('m0_nominal',selection.a.DataFrame.Histo1D(('m0_nominal','Lead jet mass after snapshot',50,0,250),'m0_nominal','weight__nominal'))

    for t in ['deepTag','particleNet']:
        top_tagger = '%s_TvsQCD'%t
	
	#   2) immediately after applying the standard top tag cut
	selection.a.SetActiveNode(baseNode)
	selection.ApplyTopPick(tagger=top_tagger,invert=False)
	selection.a.Define('m0_tight','Top_msoftdrop_corrT')
	massPlots.Add('m0_tight',selection.a.DataFrame.Histo1D(('m0_tight','Lead jet mass after top pick',50,0,250),'m0_tight','weight__nominal'))

        #   3) immediately after applying the loose (but not tight) top tag cut
	selection.a.SetActiveNode(baseNode)
	selection.ApplyTopPick(tagger=top_tagger,invert=True)
	selection.a.Define('m0_loose','Top_msoftdrop_corrT')
	massPlots.Add('m0_loose',selection.a.DataFrame.Histo1D(('m0_loose','Lead jet mass after loose cut',50,0,250),'m0_loose','weight__nominal'))

    massPlots.Do('Write')
    print('Processing time: {} sec'.format(time.time()-start))

if __name__ == "__main__":
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
    args.trigEff = Correction("TriggerEff"+args.era,'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_%s.root'%args.era,'Pretag'], corrtype='weight')
    CompileCpp('THmodules.cc')
    leadMass(args)


    











