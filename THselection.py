import ROOT, time
from TIMBER.Analyzer import HistGroup, Correction, Node
from TIMBER.Tools.Common import CompileCpp
from collections import OrderedDict
import TIMBER.Tools.AutoJME as AutoJME
from THClass import THClass

def selection(args):
    print('PROCESSING: {} {}'.format(args.setname, args.year))
    start = time.time()

    selection = THClass('dijet_nano/{}_{}_snapshot.txt'.format(args.setname,args.year), args.year, int(args.ijob), int(args.njobs))

    # automatically applies corrections from columns stored in the snapshot files
    selection.OpenForSelection(args.variation)

    # Apply HT cut due to improved trigger effs (OUTDATED, HT CUT SHOULD ALWAYS BE ZERO)
    selection.a.Cut('HT_cut','HT > {}'.format(args.HT))

    # Apply trigger efficiencies
    selection.ApplyTrigs(args.trigEff)

    if (args.njobs == '1'):
        outFileName = 'rootfiles/THselection_HT{}_{}_{}{}.root'.format(args.HT, args.setname, args.year, '_'+args.variation if args.variation != 'None' else '')
    else:
        'rootfiles/THselection_HT{}_{}_{}{}_{}of{}.root'.format(args.HT, args.setname, args.year, '_'+args.variation if args.variation != 'None' else '',args.ijob,args.njobs)

    ##################################################################################
    # Logic to determine whether to apply (mis)tagging SFs or just raw tagger scores #
    # to pick the top/phi candidates                                                 #
    ##################################################################################
    if ('Tprime' in args.setname) or ('ttbar' in args.setname):
        # Code to perform gen matching and SF application
        CompileCpp('ParticleNetSFs/TopMergingFunctions.cc')
        CompileCpp('ParticleNetSFs/PNetTopSFHandler.cc')
        CompileCpp('ParticleNetSFs/PNetPhiSFHandler.cc')
        # Perform gen matching to both candidates
        selection.a.Define('Dijet_GenMatchCats','classifyProbeJets({0,1}, Dijet_phi, Dijet_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother)')
        # Determine which variations should be applied
        if 'Tprime' in args.setname: category = 'signal'
        elif 'ttbar' in args.setname: category = 'ttbar'
        else: category = 'other' # will not happen here
        if (category != 'other'):
            print(args.variation)
            if (args.variation == 'PNetXbb_up'):
                HbbVar = 1
                TopVar = 0
            elif (args.variation == 'PNetXbb_down'):
                HbbVar = 2
                TopVar = 0
            elif (args.variation == 'PNetTop_up'):
                HbbVar = 0
                TopVar = 1
            elif (args.variation == 'PNetTop_down'):
                HbbVar = 0
                TopVar = 2
            # We are tagging the phi cand as a top, so we will just use HbbVar as the variable to track up/down
            # and use TopVar to track only the ParticleNet (mis)tagging SFs
            elif (args.variation == 'DAK8Top_up'):
                HbbVar = 1
                TopVar = 0
            elif (args.variation == 'DAK8Top_down'):
                HbbVar = 2
                TopVar = 0
            else:
                HbbVar = 0
                TopVar = 0
        # Path to efficiency file
        eosdir = 'root://cmseos.fnal.gov//store/user/ammitra/topHBoostedAllHad/TaggerEfficiencies'
        effpath = '%s/%s_%s_Efficiencies.root'%(eosdir, args.setname, args.year)
        # Instantiate the PNet SF applicators
        t_wp = 0.94
        h_wp = 0.98
        # DAK8 top wps
        if (args.year == "16") or (args.year == "16APV"):
            dak8t_wp = 0.889
        elif (args.year == "17"):
            dak8t_wp = 0.863
        elif (args.year == "18"):
            dak8t_wp = 0.92
        TopSFHandler_args = 'PNetTopSFHandler TopSFHandler = PNetTopSFHandler("%s", "%s", "%s", %f, 12345);'%(args.year, category, effpath, t_wp)
        PhiSFHandler_args = 'PNetPhiSFHandler PhiSFHandler = PNetPhiSFHandler("%s", "%s", "%s", "%s", 12345);'%(args.year, category, effpath, h_wp)
        DAKSFHandler_args = 'DAK8PhiSFHandler DAKSFHandler = DAK8PhiSFHandler("%s", "%s", "%s", 12345);'%(args.year, effpath, dak8t_wp)

        print('Instantiating PNetTopSFHandler object:\n\t%s'%TopSFHandler_args)
        CompileCpp(TopSFHandler_args)
        print('Instantiating PNetPhiSFHandler object:\n\t%s'%PhiSFHandler_args)
        CompileCpp(PhiSFHandler_args)
        print('Instantiating DAK8PhiSFHandler object:\n\t%s'%DAKSFHandler_args)
    else:
        # Define variables here so script doesn't complain later
        category = 'other'
        HbbVar = 0
        TopVar = 0
        # Used to pick Top, Phi for non-ttbar/signal files (VJets, data)
        CompileCpp("THmodules.cc")

    # Check which corrections are being tracked
    print('Tracking corrections: \n%s'%('\n\t- '.join(list(selection.a.GetCorrectionNames()))))

    # Create a checkpoint with the proper event weights
    kinOnly = selection.a.MakeWeightCols(correctionNames = list(selection.a.GetCorrectionNames()), extraNominal='' if selection.a.isData else str(selection.GetXsecScale()))

    # Prepare a root file to save the templates
    out = ROOT.TFile.Open(outFileName, 'RECREATE')
    out.cd()

    # Now define the SR and CR
    for region in ['SR', 'CR', 'ttbarCR']:
        print(HbbVar)
        print('------------------------------------------------------------------------------------------------')
        print('                         Performing selection in %s'%region)
        print('------------------------------------------------------------------------------------------------')
        selection.a.SetActiveNode(kinOnly)
        print('Selecting candidate %stop in %s...'%('(anti-)' if region == 'CR' else '', region))
        # NOTE: pass in dummy vector for the genMatch category for all non-signal/ttbar processes
        selection.Pick_Top_candidate(
            region                  = region,
            TopSFHandler_obj        = 'TopSFHandler',
            TvsQCD_discriminant     = 'Dijet_particleNet_TvsQCD',       # raw TvsQCD score from PNet
            HbbvsQCD_discriminant   = 'Dijet_particleNetMD_HbbvsQCD',   # raw HbbvsQCD score from PNet
            corrected_pt            = 'Dijet_pt_corr',                  # corrected pt
            dijet_eta               = 'Dijet_eta',                      # eta
            corrected_mass          = 'Dijet_msoftdrop_corrT',          # corrected softdrop mass
            genMatchCats            = 'Dijet_GenMatchCats' if category != 'other' else '{-1, -1}',             # gen-match jet cats from `TopMergingFuncions.cc`
            TopSFVariation          = TopVar,                                #   0:nominal, 1:up, 2:down
            invert                  = False if region == 'SR' else True,                            # False:SR, True:QCD CR
            mass_window             = [150., 200.]
        )

        # At this point we will have defined the (anti)Top and Phi candidate (by proxy).
        # The above method defines new TIMBRE subcollections for the top/phi cands using Top,Higgs as prefixes
        # We must now apply the pass and fail Hbb tagging cuts to create the QCDCR and SR, and DAK8Top cut to 
        # create the ttbarCR for the final search.
        print('Defining Fail and Pass categories based on Phi candidate score in %s...'%region)
        PassFail = selection.Pick_Phi_candidate(
            region              = region,
            PhiSFHandler_obj    = 'PhiSFHandler',
            Hbb_discriminant    = 'Higgs_particleNetMD_HbbvsQCD',
            Top_discriminant    = 'Higgs_deepTagMD_TvsQCD',
            corrected_pt        = 'Higgs_pt_corr',
            jet_eta             = 'Higgs_eta',
            genMatchCat         = 'Higgs_GenMatchCats' if category != 'other' else '-1',
            phi_variation       = HbbVar, # this is used for both PNetPhi and DAK8Phi
        )

        # We now have an ordered dictionary of pass/fail regions and the associated TIMBER nodes.
        # We will use this to construct 2D templates for each region and systematic variation.
        binsX = [50,60,560]
        binsY = [27,800,3500]
        for pf_region, node in PassFail.items():
            print('Generating 2D templates for region %s...'%(pf_region))
            mod_name  = '%s_%s'%(region,pf_region)
            mod_title = '%s %s'%(region,pf_region)
            selection.a.SetActiveNode(node)
            print('\tEvaluating %s'%mod_title)
            mTprime = 'mth'
            mPhi    = 'Higgs_msoftdrop_corrH'
            templates = selection.a.MakeTemplateHistos(ROOT.TH2F('MHvMTH_%s'%mod_name, 'MH vs MTH %s'%(mod_title),binsX[0],binsX[1],binsX[2],binsY[0],binsY[1],binsY[2]),[mPhi,mTprime])
            templates.Do('Write')

    # Save out cutflow information from selection
    cuts = ['NBEFORE_TOP_PICK_SR','NBEFORE_TOP_PICK_CR','NBEFORE_TOP_PICK_TTCR','NAFTER_TOP_PICK_SR','NAFTER_TOP_PICK_CR','NAFTER_TOP_PICK_TTCR','NBEFORE_H_PICK_SR','NBEFORE_H_PICK_CR','NBEFORE_H_PICK_TTCR','NAFTER_H_PICK_SR_FAIL','NAFTER_H_PICK_SR_PASS','NAFTER_H_PICK_CR_FAIL','NAFTER_H_PICK_CR_PASS','NAFTER_H_PICK_TTCR_FAIL','NAFTER_H_PICK_TTCR_PASS']
    hCutflow = ROOT.TH1F('cutflow','Number of events after each cut',len(cuts),0.5,len(cuts)+0.5)
    nBin = 1
    for cut in cuts:
        print('Obtaining cutflow for %s'%cut)
        nCut = getattr(selection, cut).GetValue()
        print('\t%s \t= %s'%(cut,nCut))
        hCutflow.GetXaxis().SetBinLabel(nBin, cut)
        hCutflow.AddBinContent(nBin, nCut)
        nBin += 1
    print('Writing cutflow histogram to file...')
    hCutflow.Write()
    print('Finished writing cutflow histogram to file.')
    # Done!
    out.Close()
    print('Script finished')


if __name__ == '__main__':
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
    parser.add_argument('--HT', type=str, dest='HT',
                        action='store', default='0',
                         help='Value of HT to cut on')
    # FOR DEBUGGING
    parser.add_argument('-n', type=str, dest='njobs',
                        action='store', default='1',
                        help='Number of jobs to split the total files into')
    parser.add_argument('-j', type=int, dest='ijob',
                        action='store', default=1,
                        help='Which job to run on')

    args = parser.parse_args()

    # Updated method using the trigger efficiencies parameterized by 2D function
    if ('Data' not in args.setname) and (args.year == '17'): # we are dealing with MC from 2017
        cutoff = 0.11655        # fraction of total JetHT data belonging to 2017B
        TRand = ROOT.TRandom()
        rand = TRand.Uniform(0.0, 1.0)
        if rand < cutoff:       # apply the 2017B trigger efficiency to this MC
            print('Applying 2017B trigger efficiency')
            args.trigEff = Correction("TriggerEff17",'EffLoader_2DfittedHist.cc',['out_Eff_2017B.root','Eff_2017B'],corrtype='weight')
        else:
            args.trigEff = Correction("TriggerEff17",'EffLoader_2DfittedHist.cc',['out_Eff_2017.root','Eff_2017'],corrtype='weight')
    else:
        if args.year == '16APV': year = '16'
        else: year = args.year
        args.trigEff = Correction("TriggerEff%s"%year,'EffLoader_2DfittedHist.cc',['out_Eff_20%s.root'%year,'Eff_20%s'%year],corrtype='weight')

    CompileCpp('THmodules.cc')

    selection(args)
