import ROOT, time
from TIMBER.Analyzer import HistGroup, Correction, Node
from TIMBER.Tools.Common import CompileCpp
from collections import OrderedDict
import TIMBER.Tools.AutoJME as AutoJME
from THClass import THClass
from memory_profiler import profile

@profile
def selection(args):
    print(f'Processing {args.setname} {args.year} for selection and 2D histogram creation.....')
    start = time.time()
    selection = THClass(f'dijet_nano/{args.setname}_{args.year}_snapshot.txt', args.year, int(args.ijob), int(args.njobs))
    # Automatically apply corrections from the columns stored in the snapshot files
    selection.OpenForSelection(args.variation)
    # Apply trigger efficiencies
    selection.ApplyTrigs(args.trigEff)
    # Apply tagging (signal, ttbarMC in ttCR) or mistagging (ttbarMC) scale factors
    eosdir  = 'root://cmseos.fnal.gov//store/user/ammitra/topHBoostedAllHad/TaggerEfficiencies'
    effpath = f'{eosdir}/{args.setname}_{args.year}_Efficiencies.root'

    PNetMD_HbbvsQCD_wp = 0.98
    PNet_TvsQCD_wp = 0.94
    if ('16' in args.year):
        DAK8_TvsQCD_wp      = 0.889
        DAK8_TvsQCD_wp_str  = '889'
    elif (args.year == '17'):
        DAK8_TvsQCD_wp      = 0.863
        DAK8_TvsQCD_wp_str  = '863'
    elif (args.year == '18'):
        DAK8_TvsQCD_wp      = 0.92
        DAK8_TvsQCD_wp_str  = '92'

    if ('ttbar' in args.setname) or ('TprimeB' in args.setname):
        CompileCpp('ParticleNetSFs/TopMergingFunctions.cc')
        selection.a.Define('Dijet_GenMatchCats','classifyProbeJets({0,1}, Dijet_phi, Dijet_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother)')
        if ('ttbar' in args.setname):
            # DAK8 top tagging correction for ttbarCR
            DAK8_tagging_corr = Correction(
                name        = 'DAK8_Top_tag',
                script      = 'ParticleNetSFs/DAK8TopSF_weight.cc',
                constructor = [args.year, effpath, DAK8_TvsQCD_wp_str, DAK8_TvsQCD_wp],
                mainFunc    = 'eval',
                corrtype    = 'weight',
                columnList  = ['Dijet_pt_corr', 'Dijet_eta', 'Dijet_deepTagMD_TvsQCD', 'Dijet_GenMatchCats']
            )
            selection.a.AddCorrection(
                correction  = DAK8_tagging_corr,
                evalArgs    = {'pt':'Dijet_pt_corr', 'eta':'Dijet_eta', 'DAK8_score':'Dijet_deepTagMD_TvsQCD', 'jetCat':'Dijet_GenMatchCats'}
            )
            # PNet Xbb mistagging correction for all regions
            PNet_mistagging_corr = Correction(
                name        = 'PNetMD_Xbb_mistag',
                script      = 'ParticleNetSFs/PNetXbbSF_weight.cc',
                constructor = [args.year, 'ttbar', effpath, PNetMD_HbbvsQCD_wp], # Note that we are telling the class to calculate ttbar mistag weights
                mainFunc    = 'eval',
                corrtype    = 'weight',
                columnList  = ['Dijet_pt_corr', 'Dijet_eta', 'Dijet_particleNetMD_HbbvsQCD', 'Dijet_GenMatchCats']
            )
            selection.a.AddCorrection(
                correction  = PNet_mistagging_corr,
                evalArgs    = {'pt':'Dijet_pt_corr', 'eta':'Dijet_eta', 'PNetXbb_score':'Dijet_particleNetMD_HbbvsQCD', 'jetCat':'Dijet_GenMatchCats'}
            )
        elif ('Tprime' in args.setname):
            # PNet Xbb tagging correction 
            PNet_XbbTagging_corr = Correction(
                name        = 'PNetMD_Xbb_tag',
                script      = 'ParticleNetSFs/PNetXbbSF_weight.cc',
                constructor = [args.year, 'signal', effpath, PNetMD_HbbvsQCD_wp], # Note that we are telling the class to calculate signal tag weights
                mainFunc    = 'eval',
                corrtype    = 'weight',
                columnList  = ['Dijet_pt_corr', 'Dijet_eta', 'Dijet_particleNetMD_HbbvsQCD', 'Dijet_GenMatchCats']
            )
            selection.a.AddCorrection(
                correction  = PNet_XbbTagging_corr,
                evalArgs    = {'pt':'Dijet_pt_corr', 'eta':'Dijet_eta', 'PNetXbb_score':'Dijet_particleNetMD_HbbvsQCD', 'jetCat':'Dijet_GenMatchCats'}
            )

            selection.a.DataFrame.Display(['PNetMD_Xbb_tag__nom']).Print()

            # PNet Top tagging correction
            PNet_TopTagging_corr = Correction(
                name        = 'PNet_Top_tag',
                script      = 'ParticleNetSFs/PNetTopSF_weight.cc',
                constructor = [args.year, effpath, PNet_TvsQCD_wp],
                mainFunc    = 'eval',
                corrtype    = 'weight',
                columnList  = ['Dijet_pt', 'Dijet_eta', 'Dijet_particleNet_TvsQCD', 'Dijet_GenMatchCats'],
            )
            selection.a.AddCorrection(
                correction = PNet_TopTagging_corr,
                evalArgs   = {'pt':'Dijet_pt_corr', 'eta':'Dijet_eta', 'PNetTvsQCD_score':'Dijet_particleNet_TvsQCD', 'jetCat':'Dijet_GenMatchCats'}
            )

            selection.a.DataFrame.Display(['PNet_Top_tag__nom']).Print()

    # Having added the tagging and mistagging SFs to the appropriate processes, make uncertainty columns
    print('Tracking corrections: \n%s'%('\n\t- '.join(list(selection.a.GetCorrectionNames()))))
    kinOnly = selection.a.MakeWeightCols(
        correctionNames = list(selection.a.GetCorrectionNames()),
        extraNominal = '' if selection.a.isData else str(selection.GetXsecScale())
    )

    # save all of the weight columns
    corrs = list(selection.a.GetCorrectionNames())
    cols = []
    for corr in corrs:
        if corr == 'genW': continue
        for var in ['nom','up','down']:
            cols.append(f'{corr}__{var}')           # the individual correction
            cols.append(f'weight__{corr}_{var}')    # the weight column calculated by MakeWeightCols()
    cols.append('weight__nominal')
    selection.a.Snapshot(cols,f'TEST_PNET_SYSTS_{args.setname}_{args.year}.root','Events')


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-s', type=str, dest='setname',
                        action='store', required=True,
                        help='Setname to process.')
    parser.add_argument('-y', type=str, dest='year',
                        action='store', required=True,
                        help='Year of set (16, 17, 18).')
    parser.add_argument('-v', type=str, dest='variation',
                        action='store', default='None',
                        help='JES_up, JES_down, JMR_up,...')
    # FOR DEBUGGING
    parser.add_argument('-n', type=int, dest='njobs',
                        action='store', default='1',
                        help='Number of jobs to split the total files into')
    parser.add_argument('-j', type=int, dest='ijob',
                        action='store', default=1,
                        help='Which job to run on')
    parser.add_argument('--verbose', dest='verbose',
                        action='store_true', help='Enable RDF verbosity')
    parser.add_argument('--plot', dest='plot',
                        action='store_true', help='Plot the template uncertainty histograms')

    args = parser.parse_args()
    if args.verbose:
        verbosity = ROOT.Experimental.RLogScopedVerbosity(ROOT.Detail.RDF.RDFLogChannel(), ROOT.Experimental.ELogLevel.kDebug+10)
    if ('Data' not in args.setname):
        trigyear = args.year if 'APV' not in args.setname else '16'
        args.trigEff = Correction(
            name        = f'TriggerEff{trigyear}', 
            script      = 'EffLoader_2DfittedHist.cc', 
            constructor = [f'out_Eff_20{trigyear}.root', f'Eff_20{trigyear}'],
            corrtype    = 'weight'
        )
    CompileCpp('THmodules.cc')
    selection(args)
