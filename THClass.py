import ROOT
from TIMBER.Analyzer import Correction, CutGroup, ModuleWorker, analyzer
from TIMBER.Tools.Common import CompileCpp, OpenJSON
from TIMBER.Tools.AutoPU import ApplyPU
from helpers import SplitUp
import TIMBER.Tools.AutoJME as AutoJME
from collections import OrderedDict

AutoJME.AK8collection = 'Dijet'

class THClass:
    def __init__(self,inputfile,year,ijob,njobs):
        if inputfile.endswith('.txt'): 
            infiles = SplitUp(inputfile, njobs)[ijob-1]
            print('Running on \n\t%s'%(',\n\t'.join(infiles)))
        else:
            infiles = inputfile
        '''
        # there is an issue with empty events TTrees, so make sure they don't make it through to the analyzer (mainly seen in V+Jets, esp at low HT)
        invalidFiles = []
        for iFile in infiles:
        #print('Adding {} to Analyzer'.format(iFile))
            f = ROOT.TFile.Open(iFile)
            if not f.Get('Events'):
                print('\tWARNING: {} has no Events TTree - will not be added to analyzer'.format(iFile))
                invalidFiles.append(iFile)
                continue
            if not f.Get('Events').GetEntry():
                print('\tWARNING: {} has an empty Events TTree - will not be added to analyzer'.format(iFile))
                invalidFiles.append(iFile)
            f.Close()
        inputFiles = [i for i in infiles if i not in invalidFiles]
        if len(inputFiles) == 0:
            print("\n\t WARNING: None of the files given contain an Events TTree.")
            self.a = analyzer(inputFiles)
        else:
            infiles = inputfile
            self.a = analyzer(infiles)

        if inputfile.endswith('.txt'):
            self.setname = inputfile.split('/')[-1].split('_')[0]
        else:
            self.setname = inputfile.split('/')[-1].split('_')[1]
        '''

        self.setname = inputfile.split('/')[-1].split('_')[0]
        self.a = analyzer(infiles)

        self.year = str(year)    # most of the time this class will be instantiated from other scripts with CLI args, so just convert to string for internal use
        self.ijob = ijob
        self.njobs = njobs
        self.config = OpenJSON('THconfig.json')
        self.cuts = self.config['CUTS']
        self.newTrigs = self.config['TRIGS']    
        self.trigs = {
        16:['HLT_PFHT800','HLT_PFHT900'],
            17:["HLT_PFHT1050","HLT_AK8PFJet500","HLT_AK8PFHT750_TrimMass50","HLT_AK8PFHT800_TrimMass50","HLT_AK8PFJet400_TrimMass30"],
            19:['HLT_PFHT1050','HLT_AK8PFJet500'], # just use 19 for trigger script for 17b, 17all
            #18:["HLT_PFHT1050","HLT_AK8PFHT800_TrimMass50","HLT_AK8PFJet500","HLT_AK8PFJet400_TrimMass30","HLT_AK8PFHT750_TrimMass50"]
            18:['HLT_AK8PFJet400_TrimMass30','HLT_AK8PFHT850_TrimMass50','HLT_PFHT1050']
        }

        if 'Data' in inputfile:        # SingleMuonDataX_year and DataX_year are possible data inputfile names
            self.a.isData = True
        else:
            self.a.isData = False

    def GetXsecScale(self):
        lumi = self.config['lumi{}'.format(self.year)]
        xsec = self.config['XSECS'][self.setname]
        if self.a.genEventSumw == 0:
            raise ValueError('%s %s: genEventSumw is 0'%(self.setname, self.year))
        print('Normalizing by lumi*xsec/genEventSumw:\n\t{} * {} / {} = {}'.format(lumi,xsec,self.a.genEventSumw,lumi*xsec/self.a.genEventSumw))
        return lumi*xsec/self.a.genEventSumw

    def AddCutflowColumn(self, var, varName):
        '''
        for future reference:
        https://root-forum.cern.ch/t/rdataframe-define-column-of-same-constant-value/34851
        '''
        print('Adding cutflow information...\n\t{}\t{}'.format(varName, var))
        self.a.Define('{}'.format(varName),str(var))

    def getNweighted(self):
        # Avoid executing the event loop via GetValue(), instead just get the RResultPtr and call it later
        if not self.a.isData:
            #return self.a.DataFrame.Sum("genWeight").GetValue()
            return self.a.DataFrame.Sum("genWeight")
        else:
            #return self.a.DataFrame.Count().GetValue()
            return self.a.DataFrame.Count()

    ####################
    # Snapshot related #
    ####################
    def ApplyKinematicsSnap(self): # For snapshotting only
        # total number processed
        #self.NPROC = self.a.genEventSumw    # follow Matej https://github.com/mroguljic/X_YH_4b/blob/9602da767d1c1cf0e9fc19bade7b104b1da40212/eventSelection.py#L90
        self.NPROC = self.getNweighted()
        #self.AddCutflowColumn(self.NPROC, "NPROC")

        flags = [
            'Flag_goodVertices',
            'Flag_globalSuperTightHalo2016Filter',
            'Flag_HBHENoiseFilter',
            'Flag_HBHENoiseIsoFilter',
            'Flag_EcalDeadCellTriggerPrimitiveFilter',
            'Flag_BadPFMuonFilter',
            'Flag_BadPFMuonDzFilter',
            'Flag_eeBadScFilter'
        ]
        if self.year == '17' or self.year == '18':
            flags.append('Flag_ecalBadCalibFilter')
        MET_filters = self.a.GetFlagString(flags)    # string valid (existing in RDataFrame node) flags together w logical and
        self.a.Cut('flags', MET_filters)
        self.NFLAGS = self.getNweighted()
        #self.AddCutflowColumn(self.NFLAGS, "NFLAGS")

        self.a.Cut('njets','nFatJet >= 2')
        self.NJETS = self.getNweighted()
        #self.AddCutflowColumn(self.NJETS, "NJETS")

        # jetId cut: https://cms-pub-talk.web.cern.ch/t/jme-or/6547
        # INFO: https://twiki.cern.ch/twiki/bin/viewauth/CMS/JetID#nanoAOD_Flags
        self.a.Cut('jetId', 'Jet_jetId[0] > 1 && Jet_jetId[1] > 1')    # drop any events whose dijets did not both pass tight jetId requirement
        self.NJETID = self.getNweighted()
        #self.AddCutflowColumn(self.NJETID, "NJETID")

        self.a.Cut('pT', 'FatJet_pt[0] > {0} && FatJet_pt[1] > {0}'.format(self.cuts['pt']))
        self.NPT = self.getNweighted()
        #self.AddCutflowColumn(self.NPT, "NPT")

        self.a.Define('DijetIdxs','PickDijets(FatJet_pt, FatJet_eta, FatJet_phi, FatJet_msoftdrop)')
        self.a.Cut('dijetsExist','DijetIdxs[0] > -1 && DijetIdxs[1] > -1')
        self.NKIN = self.getNweighted()
        #self.AddCutflowColumn(self.NKIN, "NKIN")

        self.a.SubCollection('Dijet','FatJet','DijetIdxs',useTake=True)
        self.a.Define('Dijet_vect','hardware::TLvector(Dijet_pt, Dijet_eta, Dijet_phi, Dijet_msoftdrop)')

        #print(self.a.GetCollectionNames())

        # This cut might kill too much signal, just add it later if need-be
        '''
        self.a.Define('deltaEta','abs(Dijet_eta[0]-Dijet_eta[1])')
        self.a.Cut('deltaEta_cut','deltaEta < 1.6')
        self.NDELTAETA = self.getNweighted()
        #self.AddCutflowColumn(self.NDELTAETA,'NDELTAETA')
        '''
        return self.a.GetActiveNode()

    def ApplyStandardCorrections(self,snapshot=False):
        if snapshot:
            if self.a.isData:
                lumiFilter = ModuleWorker('LumiFilter','TIMBER/Framework/include/LumiFilter.h',[int(self.year) if 'APV' not in self.year else 16])
                self.a.Cut('lumiFilter',lumiFilter.GetCall(evalArgs={"lumi":"luminosityBlock"}))
                if self.year == '18':
                    # need to get same setname for single muon datasets, i.e. SingleMuonDataX_18 -> DataX (perform string slice)
                    HEM_worker = ModuleWorker('HEM_drop','TIMBER/Framework/include/HEM_drop.h',[self.setname if 'Muon' not in self.setname else self.setname[10:]])
                    self.a.Cut('HEM','%s[0] > 0'%(HEM_worker.GetCall(evalArgs={"FatJet_eta":"Dijet_eta","FatJet_phi":"Dijet_phi"})))

            else:
                # Parton shower weights
                #       - https://twiki.cern.ch/twiki/bin/viewauth/CMS/TopSystematics#Parton_shower_uncertainties
                #       - "Default" variation: https://twiki.cern.ch/twiki/bin/view/CMS/HowToPDF#Which_set_of_weights_to_use
                #       - https://github.com/mroguljic/Hgamma/blob/409622121e8ab28bc1072c6d8981162baf46aebc/templateMaker.py#L210
                self.a.Define("ISR__up","PSWeight[2]")
                self.a.Define("ISR__down","PSWeight[0]")
                self.a.Define("FSR__up","PSWeight[3]")
                self.a.Define("FSR__down","PSWeight[1]")
                # Add the genWeight branch as a correction to all event weights
                genWCorr    = Correction('genW','TIMBER/Framework/TopPhi_modules/BranchCorrection.cc',corrtype='corr',mainFunc='evalCorrection') # workaround so we can have multiple BCs
                self.a.AddCorrection(genWCorr, evalArgs={'val':'genWeight'})
                ISRcorr = genWCorr.Clone("ISRunc",newMainFunc="evalUncert",newType="uncert")
                FSRcorr = genWCorr.Clone("FSRunc",newMainFunc="evalUncert",newType="uncert")
                self.a.AddCorrection(ISRcorr, evalArgs={'valUp':'ISR__up','valDown':'ISR__down'})
                self.a.AddCorrection(FSRcorr, evalArgs={'valUp':'FSR__up','valDown':'FSR__down'})
                # QCD factorization and renormalization corrections (only apply to non-signal MC in fit, but generate it here just in case...)
                # First instatiate a correction module for the factorization correction
                facCorr = Correction('QCDscale_factorization','LHEScaleWeights.cc',corrtype='weight',mainFunc='evalFactorization')
                self.a.AddCorrection(facCorr, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})
                # Now clone it and call evalRenormalization for the renormalization correction
                renormCorr = facCorr.Clone('QCDscale_renormalization',newMainFunc='evalRenormalization',newType='weight')
                self.a.AddCorrection(renormCorr, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})
                # Now do one for the combined correction
                combCorr = facCorr.Clone('QCDscale_combined',newMainFunc='evalCombined',newType='weight')
                self.a.AddCorrection(combCorr, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})
                # And finally, do one for the uncertainty
                # See: https://indico.cern.ch/event/938672/contributions/3943718/attachments/2073936/3482265/MC_ContactReport_v3.pdf (slide 27)
                QCDScaleUncert = facCorr.Clone('QCDscale_uncert',newMainFunc='evalUncert',newType='uncert')
                self.a.AddCorrection(QCDScaleUncert, evalArgs={'LHEScaleWeights':'LHEScaleWeight'})
                # Apply pileup reweighting to everything
                self.a = ApplyPU(self.a, 'THpileup.root', self.year, ULflag=True, histname='{}_{}'.format(self.setname,self.year))
                self.a.AddCorrection(
                    Correction('Pdfweight','TIMBER/Framework/include/PDFweight_uncert.h',[self.a.lhaid],corrtype='uncert')
                )
                if self.year == '16' or self.year == '17' or self.year == '16APV':
                    # The column names are: L1PreFiringWeight_Up, L1PreFiringWeight_Dn, L1PreFiringWeight_Nom
                    L1PreFiringWeight = genWCorr.Clone('L1PreFireWeight',newMainFunc='evalWeight',newType='weight')
                    self.a.AddCorrection(L1PreFiringWeight, evalArgs={'val':'L1PreFiringWeight_Nom','valUp':'L1PreFiringWeight_Up','valDown':'L1PreFiringWeight_Dn'})

                elif self.year == '18':
                    self.a.AddCorrection(
                        Correction('HEM_drop','TIMBER/Framework/include/HEM_drop.h',[self.setname],corrtype='corr')
                    )

                if 'ttbar' in self.setname:
                    self.a.Define('GenParticle_vect','hardware::TLvector(GenPart_pt, GenPart_eta, GenPart_phi, GenPart_mass)')
                    self.a.AddCorrection(
                        Correction('TptReweight','TIMBER/Framework/include/TopPt_weight.h',corrtype='weight'),
                        evalArgs={
                            "jet0":"Dijet_vect[0]",
                            "jet1":"Dijet_vect[1]",
                            'GenPart_vect':'GenParticle_vect'
                        }
                    )
            # need to account for Single Muon datasets having a differnt setname, i.e. SingleMuonDataX_year
            if ('Muon' in self.setname):
                self.a = AutoJME.AutoJME(self.a, 'Dijet', '20'+self.year, self.setname[10:])
            else:
                # regardless of passing self.setname, the AutoJME function will check if input is data or not
                self.a = AutoJME.AutoJME(self.a, 'Dijet', '20'+self.year, self.setname)

            #self.a.MakeWeightCols(extraNominal='genWeight' if not self.a.isData else '')
            # since we added genWcorr we do not have to do anything else with extraNominal genWeight correction
            self.a.MakeWeightCols() # this is actually not necessary for the snapshot stage, but just do it to check the stdout that all makes sense. 

        else:
            if not self.a.isData:
                # I forgot to add the `genW` branch in snapshots, so just redo it here...
                # In the end it doesn't really matter, since the correction just uses genWeight.
                # One could also opt to add genWeight*GetXsecScale() in the MakeWeightCols() call as well..                        # This is EXTREMELY IMPORTANT for getting the event weighting correct
                # Add the genWeight branch as a correction to all event weights
                genWCorr    = Correction('genW','TIMBER/Framework/TopPhi_modules/BranchCorrection.cc',corrtype='corr',mainFunc='evalCorrection') # workaround so we can have multiple BCs
                self.a.AddCorrection(genWCorr, evalArgs={'val':'genWeight'})


                self.a.AddCorrection(Correction('Pileup',corrtype='weight'))
                self.a.AddCorrection(Correction('ISRunc',corrtype='uncert'))
                self.a.AddCorrection(Correction('FSRunc',corrtype='uncert'))
                self.a.AddCorrection(Correction('Pileup',corrtype='weight'))
                self.a.AddCorrection(Correction('Pdfweight',corrtype='uncert'))
                if self.year == '16' or self.year == '17' or self.year == '16APV':
                    self.a.AddCorrection(Correction('L1PreFireWeight',corrtype='weight'))
                elif self.year == '18':
                    self.a.AddCorrection(Correction('HEM_drop',corrtype='corr'))
                if 'ttbar' in self.setname:
                    self.a.AddCorrection(Correction('TptReweight',corrtype='weight'))
                self.a.AddCorrection(Correction('QCDscale_factorization',corrtype='weight'))
                self.a.AddCorrection(Correction('QCDscale_renormalization',corrtype='weight'))
                self.a.AddCorrection(Correction('QCDscale_combined',corrtype='weight'))
                self.a.AddCorrection(Correction('QCDscale_uncert',corrtype='uncert'))
                
        return self.a.GetActiveNode()

    #################################
    # For lepton veto orthogonality #
    #################################
    def LeptonVeto(self):
        '''
        Semileptonic search has the following leptonic preselection:
        TightLeptons
            tightMu = list(filter(lambda x : x.tightId and x.pt>30 and x.pfRelIso04_all<0.15 and abs(x.eta)<2.4,muon))
            tightEl = list(filter(lambda x : x.mvaFall17V2Iso_WP80 and x.pt>35 and abs(x.eta)<2.5, electron))
        TopLeptons
            goodMu = list(filter(lambda x : x.pt>30 and x.looseId==1 and abs(x.dxy)<0.02 and abs(x.eta)<2.4, muons))
            goodEl = list(filter(lambda x : x.pt>35 and x.mvaFall17V2noIso_WP90==1 and abs(x.dxy)<0.05 and abs(x.eta)<2.5, electrons))
        We will invert these requirements and see how the yields are affected. However, there may be multiple leptons per event, 
        so we will first check if the event has muons (nMuon<1) and if there are, we loop over the leptons in the event and 
        immediately return true if a lepton in the event meets the veto criteria. See THmodules.cc for implementation.
        '''
        self.PreLeptonVeto = self.getNweighted()
        # tightMu inversion
        self.a.Cut('tightMu_veto','TightMuVeto(nMuon, Muon_tightId, Muon_pt, Muon_pfRelIso04_all, Muon_eta)==0')
        self.NTightMu = self.getNweighted()
        # tightEl inversion
        self.a.Cut('tightEl_veto','TightElVeto(nElectron, Electron_mvaFall17V2Iso_WP80, Electron_pt, Electron_eta)==0')
        self.NTightEl = self.getNweighted()
        # goodMu inversion
        self.a.Cut('goodMu_veto','GoodMuVeto(nMuon, Muon_pt, Muon_looseId, Muon_dxy, Muon_eta)==0')
        self.NGoodMu = self.getNweighted()
        # goodEl inversion
        self.a.Cut('goodEl_veto','GoodElVeto(nElectron, Electron_pt, Electron_mvaFall17V2noIso_WP90, Electron_dxy, Electron_eta)==0')
        self.NGoodEl = self.getNweighted()

        self.PostLeptonVeto = self.getNweighted()
        return self.a.GetActiveNode()

    def Snapshot(self,node=None, colNames=[]):
        '''
        colNames [str] (optional): list of column names to add to the snapshot 
        '''
        startNode = self.a.GetActiveNode()
        if node == None: node = self.a.GetActiveNode()

        columns = [
        'FatJet_pt', # keep this so that we can calculate the HT 
            'Dijet_eta','Dijet_msoftdrop','Dijet_pt','Dijet_phi',
            'Dijet_deepTagMD_HbbvsQCD', 'Dijet_deepTagMD_ZHbbvsQCD',
            'Dijet_deepTagMD_TvsQCD', 'Dijet_deepTag_TvsQCD', 'Dijet_particleNet_HbbvsQCD',
            'Dijet_particleNet_TvsQCD', 'Dijet_particleNetMD.*', 'Dijet_rawFactor', 'Dijet_tau*',
            'Dijet_jetId', 'nFatJet', 'Dijet_JES_nom',
            'HLT_PFHT.*', 'HLT_PFJet.*', 'HLT_AK8.*', 'HLT_Mu50', 'HLT_IsoMu*', 'HLT_Ele27_WPTight_Gsf', 'HLT_Ele35_WPTight_Gsf',
            'event', 'eventWeight', 'luminosityBlock', 'run',
            'NPROC', 'NFLAGS', 'NJETID', 'NJETS', 'NPT', 'NKIN', 'NDELTAETA', 'NTightMu', 'NTightEl', 'NGoodMu', 'NGoodEl', 'PreLeptonVeto', 'PostLeptonVeto'
        ]

        if not self.a.isData:
            columns.extend(['GenPart_.*', 'nGenPart','genWeight','GenModel*'])
            columns.extend(['PSWeight', 'LHEScaleWeight'])
            columns.extend(['Dijet_JES_up','Dijet_JES_down',
                            'Dijet_JER_nom','Dijet_JER_up','Dijet_JER_down',
                            'Dijet_JMS_nom','Dijet_JMS_up','Dijet_JMS_down',
                            'Dijet_JMR_nom','Dijet_JMR_up','Dijet_JMR_down'])
            columns.extend(['Pileup__nom','Pileup__up','Pileup__down','Pdfweight__nom','Pdfweight__up','Pdfweight__down','ISRunc__up','ISRunc__down','FSRunc__up','FSRunc__down'])
            columns.extend(['QCDscale_factorization__nom','QCDscale_factorization__up','QCDscale_factorization__down'])
            columns.extend(['QCDscale_renormalization__nom','QCDscale_renormalization__up','QCDscale_renormalization__down'])
            columns.extend(['QCDscale_combined__nom','QCDscale_combined__up','QCDscale_combined__down'])
            columns.extend(['QCDscale_uncert__up','QCDscale_uncert__down'])
            if self.year == '16' or self.year == '17' or self.year == '16APV':
                columns.extend(['L1PreFiringWeight_Nom', 'L1PreFiringWeight_Up', 'L1PreFiringWeight_Dn'])    # keep the TIMBER Prefire calculations, but also include these from NanoAODv9
                columns.extend(['L1PreFireWeight__nom','L1PreFireWeight__up','L1PreFireWeight__down'])    # these are the weight columns created by the BranchCorrection module 
            elif self.year == '18':
                columns.append('HEM_drop__nom')
            if 'ttbar' in self.setname:
                columns.extend(['TptReweight__nom','TptReweight__up','TptReweight__down'])

        if (len(colNames) > 0):
            columns.extend(colNames)

        self.a.SetActiveNode(node)
        self.a.Snapshot(columns,'THsnapshot_%s_%s_%sof%s.root'%(self.setname,self.year,self.ijob,self.njobs),'Events',openOption='RECREATE',saveRunChain=True)
        self.a.SetActiveNode(startNode)

    #####################
    # Selection related #
    #####################
    def OpenForSelection(self,variation):
        self.a.Define('Dijet_particleNetMD_HbbvsQCD','Dijet_particleNetMD_Xbb/(Dijet_particleNetMD_Xbb+Dijet_particleNetMD_QCD)')
        self.ApplyStandardCorrections(snapshot=False)
        self.a.Define('Dijet_vect_trig','hardware::TLvector(Dijet_pt, Dijet_eta, Dijet_phi, Dijet_msoftdrop)')
        self.a.Define('mth_trig','hardware::InvariantMass(Dijet_vect_trig)')
        self.a.Define('m_javg','(Dijet_msoftdrop[0]+Dijet_msoftdrop[1])/2')
        # JME variations
        if not self.a.isData:
            pt_calibs, top_mass_calibs = JMEvariationStr('Top',variation)     # the pt calibs are the same for
            pt_calibs, higgs_mass_calibs = JMEvariationStr('Higgs',variation) # top and H
            self.a.Define('Dijet_pt_corr','hardware::MultiHadamardProduct(Dijet_pt,%s)'%pt_calibs)
            self.a.Define('Dijet_msoftdrop_corrT','hardware::MultiHadamardProduct(Dijet_msoftdrop,%s)'%top_mass_calibs)
            self.a.Define('Dijet_msoftdrop_corrH','hardware::MultiHadamardProduct(Dijet_msoftdrop,%s)'%higgs_mass_calibs)
        else:
            self.a.Define('Dijet_pt_corr','hardware::MultiHadamardProduct(Dijet_pt,{Dijet_JES_nom})')
            self.a.Define('Dijet_msoftdrop_corrT','hardware::MultiHadamardProduct(Dijet_msoftdrop,{Dijet_JES_nom})')
            self.a.Define('Dijet_msoftdrop_corrH','hardware::MultiHadamardProduct(Dijet_msoftdrop,{Dijet_JES_nom})')
        # for trigger studies
        self.a.Define('pt0','Dijet_pt_corr[0]')
        self.a.Define('pt1','Dijet_pt_corr[1]')
        self.a.Define('HT','pt0+pt1')
        return self.a.GetActiveNode()

    def ApplyTrigs(self,corr=None):
        if self.a.isData:
            self.a.Cut('trigger',self.a.GetTriggerString(self.trigs[int(self.year) if 'APV' not in self.year else 16]))
        else:
            self.a.AddCorrection(corr, evalArgs={"xval":"m_javg","yval":"mth_trig"})    
        return self.a.GetActiveNode()


    #########################################################################################################
    #                               SELECTION METHODS                                                       #
    #########################################################################################################
    # Selection consists of first picking the top candidate from the two possible jets in each event, and   #
    # then picking the Higgs candidate via progressively tightening cuts on the Higgs candidate jet's       #
    # particleNetMD_HbbvsQCD score.                                                                         #
    #   - PNet top-tagging SFs are applied to signal to upgrade/downgrade jet tagging status                #
    #   - the raw PNet TvsQCD score is used to determine the tagging for everything else                    #
    # We do not have to worry about mistagging scale factors for the top tagging, only for the H-tagging    #
    #########################################################################################################
    def Pick_Top_candidate(
        self,
        region                  = 'SR',                             # 'SR','CR','ttbarCR'
        TopSFHandler_obj        = 'TopSFHandler',                   # instance of the Top SF handler C++ class
        TvsQCD_discriminant     = 'Dijet_particleNet_TvsQCD',       # raw TvsQCD score from PNet
        HbbvsQCD_discriminant   = 'Dijet_particleNetMD_HbbvsQCD',   # raw HbbvsQCD score from PNet
        corrected_pt            = 'Dijet_pt_corr',                  # corrected pt
        dijet_eta               = 'Dijet_eta',                      # eta
        corrected_mass          = 'Dijet_msoftdrop_corrT',          # corrected softdrop mass
        genMatchCats            = 'Dijet_GenMatchCats',             # gen-match jet cats from `TopMergingFuncions.cc`
        TopSFVariation          = 0,                                #   0:nominal, 1:up, 2:down
        invert                  = False,                            # False:SR, True:QCD CR
        mass_window             = [150., 200.]                      # top mass window
    ):
        assert(region in ['SR','CR','ttbarCR'])
        if (region == 'SR'):
            assert(invert == False)
        elif (region == 'CR'):
            assert(invert == True)

        # Cutflow - before top selection
        if region == 'SR':
            self.NBEFORE_TOP_PICK_SR = self.getNweighted()
        elif region == 'CR':
            self.NBEFORE_TOP_PICK_CR = self.getNweighted()
        elif region == 'ttbarCR':
            self.NBEFORE_TOP_PICK_TTCR = self.getNweighted()
        # column names for the top (anti-)candidate index
        objIdxs = 'ObjIdxs_%s'%(region)
        # Create the column containing the indices of the two jets after matching
        # This is done separately for the ttbar+signal and data/otherMC
        if ('ttbar' in self.setname) or ('Tprime' in self.setname):
            self.a.Define(objIdxs,
                '%s.Pick_Top_candidate(%s, %s, %s, %s, %s, %s, %s, %s, {%f, %f}, {0, 1})'%(
                    TopSFHandler_obj,
                    TvsQCD_discriminant,
                    HbbvsQCD_discriminant,
                    corrected_pt,
                    dijet_eta,
                    corrected_mass,
                    genMatchCats,
                    TopSFVariation,
                    'true' if invert else 'false',
                    mass_window[0],
                    mass_window[1]
                )
            )

            print('DEBUG ------------------------------------------------------------------------------------')
            print('\t%s: \t%s'%(TvsQCD_discriminant,self.a.DataFrame.GetColumnType(TvsQCD_discriminant)))
            print('\t%s: \t\t%s'%(genMatchCats,self.a.DataFrame.GetColumnType(genMatchCats)))
            print('\t%s: \t\t\t%s'%(objIdxs,self.a.DataFrame.GetColumnType(objIdxs)))
            print('------------------------------------------------------------------------------------------')

        else:
            # This assumes that `THmodules.cc` has been compiled already
            self.a.Define(objIdxs,
                'PickTopCRv2(%s, %s, %s, {0, 1}, {150., 200.}, %s, %s)'%(
                    corrected_mass,
                    TvsQCD_discriminant,
                    HbbvsQCD_discriminant,
                    0.94,
                    'true' if invert else 'false'
                )
            )

        # At this point, we'll have a column named ObjIdxs_SR/CR/ttbarCR containing the indices of which
        # of the two jets is the top and which is the Higgs (tIdx, hIdx), or {-1,-1} if at least one top 
        # doesn't pass the top tagging
        self.a.Define('tIdx','%s[0]'%(objIdxs))
        self.a.Define('hIdx','%s[1]'%(objIdxs))
        self.a.Cut('HasTop','tIdx > -1')

        # Cutflow - after top selection
        if region == 'SR':
            self.NAFTER_TOP_PICK_SR = self.getNweighted()
        elif region == 'CR':
            self.NAFTER_TOP_PICK_CR = self.getNweighted()
        elif region == 'ttbarCR':
            self.NAFTER_TOP_PICK_TTCR = self.getNweighted()
        '''
        # Now perform the top mass window cut in the SR (not used, since TvsQCD is not MD)
        if not invert:
            mTop    = '%s[tIdx]'%(corrected_mass)
            mTopCut = '({0} >= {1}) && ({0} <= {2})'.format(mTop, mass_window[0], mass_window[1])
            self.a.Cut('mTop_window',mTopCut)
            # Cutflow - after top mass requirement (SR only)
            self.NAFTER_TOP_MASS_REQ_SR = self.getNweighted()
        '''
        # At this point, rename Dijet -> Top/Higgs based on its index determined above
        self.a.ObjectFromCollection('Top','Dijet','tIdx',skip=['msoftdrop_corrH'])
        self.a.ObjectFromCollection('Higgs','Dijet','hIdx',skip=['msoftdrop_corrT'])
        self.a.Define('Top_vect','hardware::TLvector(Top_pt_corr, Top_eta, Top_phi, Top_msoftdrop_corrT)')
        self.a.Define('Higgs_vect','hardware::TLvector(Higgs_pt_corr, Higgs_eta, Higgs_phi, Higgs_msoftdrop_corrH)')
        self.a.Define('mth','hardware::InvariantMass({Top_vect,Higgs_vect})')
        return self.a.GetActiveNode()

    '''
    In the SR and CR, the "phi" candidate is naturally assigned as the second jet after the top candidate is found.
    In the ttbarCR, the "phi" candidate is supposed to be a second top, tagged by DAK8MD, in order to form a ttbar-
    dominated control region. 
    SR and CR:
        - apply a sequentially tightening cut on the phi candidate jet to obtain the Pass and Fail regions 
          (Fail = former Loose. We got rid of the original fail region since stats are too high).
        - Pass = phi score > 0.98
        - Fail = 0.8 < phi score < 0.98
    ttbarCR:
        - Pass = phi candidate fails the DAK8MD tight working point
        - Fail = phi candidate passes the DAK8MD tight working point
    '''
    def Pick_Phi_candidate(
        self,
        region              = 'SR',
        PhiSFHandler_obj    = 'PhiSFHandler',
        Hbb_discriminant    = 'Higgs_particleNetMD_HbbvsQCD',
        Top_discriminant    = 'Higgs_deepTagMD_TvsQCD',
        corrected_pt        = 'Higgs_pt_corr',
        jet_eta             = 'Higgs_eta',
        genMatchCat         = 'Higgs_GenMatchCats',
        phi_variation       = 0,
    ):
        assert(region in ['SR','CR','ttbarCR'])
        # Cutflow - before Higgs/top selection
        if region == 'SR':
            self.NBEFORE_H_PICK_SR = self.getNweighted()
        elif region == 'CR':
            self.NBEFORE_H_PICK_CR = self.getNweighted()
        elif region == 'ttbarCR':
            self.NBEFORE_H_PICK_TTCR = self.getNweighted()

        # Determine whether we are working in the ttbarCR or SR/CR. 
        # Whether we are operating on signal or ttbar will have already been determined 
        # when instantiating the SFHandler objects via a string argument.
        if region == 'ttbarCR':
            # Ensure that the ttbarCR is orthogonal to the SR by requiring PNetXbb < 0.8
            self.a.Define('SR_ttCR_orthog_cut','%s < 0.8'%Hbb_discriminant)
            if ('ttbar' in self.setname):   # tagging phi cand as top with DAK8MD tagger - apply SFs
                assert(PhiSFHandler_obj == 'DAKSFHandler')
                self.a.Define('PhiTagStatus',
                    '%s.GetNewTopCat(%s, %s, %s, %s, %s);'%(
                        PhiSFHandler_obj,
                        Top_discriminant,
                        corrected_pt,
                        jet_eta,
                        phi_variation,
                        genMatchCat
                    )
                )
            else:   # tagging phi cand as top with DAK8MD - do not apply SFs
                # this assumes `THmodules.cc` has been compiled already
                if (self.year == "16") or (self.year == "16APV"):
                    dak8t_wp = 0.889
                elif (self.year == "17"):
                    dak8t_wp = 0.863
                elif (self.year == "18"):
                    dak8t_wp = 0.92
                self.a.Define('PhiTagStatus','Pick_H_candidate_standard(%s, %s)'%(Top_discriminant, dak8t_wp))
        else:
            if ('ttbar' in self.setname) or ('Tprime' in self.setname):   
                # tagging phi cand as phi with PNet - apply tag/mistag SFs
                assert(PhiSFHandler_obj == 'PhiSFHandler')
                self.a.Define('PhiTagStatus',
                    '%s.GetNewHCat(%s, %s, %s, %s, %s)'%(
                        PhiSFHandler_obj,
                        Hbb_discriminant,
                        corrected_pt,                                                                              jet_eta,
                        phi_variation,
                        genMatchCat
                    )
                )
            else: # no tag/mistag SFs
                # this assumes `THmodules.cc` has been compiled already
                self.a.Define('PhiTagStatus','Pick_H_candidate_standard(%s, %s)'%(Hbb_discriminant, 0.98))

        if ('ttbar' in self.setname) or ('Tprime' in self.setname):
            print('DEBUG ------------------------------------------------------------------------------------')
            print('\t%s: \t%s'%(Hbb_discriminant,self.a.DataFrame.GetColumnType(Hbb_discriminant)))
            print('\t%s: \t\t%s'%(genMatchCat,self.a.DataFrame.GetColumnType(genMatchCat)))
            print('\t%s: \t\t\t%s'%('PhiTagStatus',self.a.DataFrame.GetColumnType('PhiTagStatus')))
            print('------------------------------------------------------------------------------------------')

        # At this point, we have a column describing what the tagging status of the phi candidate is:
        #   - For ttbar, mistagging SFs will have been applied to account for mistagging gen top as Hbb.
        #   - For signal, tagging SFs will have been applied to match performance of tagger in data.
        #   - for anything else, only the raw tagging score is used to determine tagged/not tagged.
        #   - for ttbar+signal, in the ttbarCR, DAK8MD tagging SFs are applied.
        # We will now be able to define the Fail and Pass regions and return them.
        out = OrderedDict()
        checkpoint = self.a.GetActiveNode()
        for pf_region in ['fail','pass']:
            print('Performing selection on phi candidate jet in %s region of %s...'%(pf_region,region))
            print('\tTagging phi candidate as %s'%('top' if region=='ttbarCR' else 'phi'))
            self.a.SetActiveNode(checkpoint)
            out[pf_region] = self.a.Cut('PhiTag_%s_%s'%(region,pf_region), 'PhiTagStatus == %s'%(0 if pf_region == 'fail' else 1))
            # Cutflow
            if region == 'SR':
                if pf_region == 'fail':
                    self.NAFTER_H_PICK_SR_FAIL = self.getNweighted()
                else:
                    self.NAFTER_H_PICK_SR_PASS = self.getNweighted()
            elif region == 'CR':
                if pf_region == 'fail':
                    self.NAFTER_H_PICK_CR_FAIL = self.getNweighted()
                else:
                    self.NAFTER_H_PICK_CR_PASS = self.getNweighted()
            elif region == 'ttbarCR':
                if pf_region == 'fail':
                    self.NAFTER_H_PICK_TTCR_FAIL = self.getNweighted()
                else:
                    self.NAFTER_H_PICK_TTCR_PASS = self.getNweighted()
        # Send out the ordered dictionary {'fail':FailNode, 'pass':PassNode}
        return out
 
    ###############
    # For studies #
    ###############
    def ApplyTopPickViaMatch(self):
        objIdxs = 'ObjIdxs_GenMatch'
        if 'GenParticle_vect' not in self.a.GetColumnNames():
            self.a.Define('GenParticle_vect','hardware::TLvector(GenPart_pt, GenPart_eta, GenPart_phi, GenPart_mass)')
        if objIdxs not in self.a.GetColumnNames():
            self.a.Define('jet_vects','hardware::TLvector(Dijet_pt, Dijet_eta, Dijet_phi, Dijet_msoftdrop)')
            self.a.Define(objIdxs,'PickTopGenMatch(jet_vects, GenParticle_vect, GenPart_pdgId)') # ignore JME variations in this study
            self.a.Define('tIdx','%s[0]'%objIdxs)
            self.a.Define('hIdx','%s[1]'%objIdxs)
        self.a.Cut('GoodMatches','tIdx > -1 && hIdx > -1')
        self.a.ObjectFromCollection('Top','Dijet','tIdx')
        self.a.ObjectFromCollection('Higgs','Dijet','hIdx')
        return self.a.GetActiveNode()

    def GetNminus1Group(self,tagger):
        # Use after ApplyTopPickViaMatch
        cutgroup = CutGroup('taggingVars')
        cutgroup.Add('mH_%s_cut'%tagger,'SubleadHiggs_msoftdrop_corrH > {0} && SubleadHiggs_msoftdrop_corrH < {1}'.format(*self.cuts['mh']))
        cutgroup.Add('mt_%s_cut'%tagger,'LeadTop_msoftdrop_corrT > {0} && LeadTop_msoftdrop_corrT < {1}'.format(*self.cuts['mt']))
        cutgroup.Add('%s_H_cut'%tagger,'SubleadHiggs_{0}MD_HbbvsQCD > {1}'.format(tagger, self.cuts[tagger+'MD_HbbvsQCD']))
        cutgroup.Add('%s_top_cut'%tagger,'LeadTop_{0}_TvsQCD > {1}'.format(tagger, self.cuts[tagger+'_TvsQCD']))
        return cutgroup

def JMEvariationStr(p,variation):
    base_calibs = ['Dijet_JES_nom','Dijet_JER_nom', 'Dijet_JMS_nom', 'Dijet_JMR_nom']
    variationType = variation.split('_')[0]
    pt_calib_vect = '{'
    mass_calib_vect = '{'
    for c in base_calibs:
        if 'JM' in c and p != 'Top':
            mass_calib_vect+='%s,'%('Dijet_'+variation if variationType in c else c)
        elif 'JE' in c:
            pt_calib_vect+='%s,'%('Dijet_'+variation if variationType in c else c)
            mass_calib_vect+='%s,'%('Dijet_'+variation if variationType in c else c)
    pt_calib_vect = pt_calib_vect[:-1]+'}'
    mass_calib_vect = mass_calib_vect[:-1]+'}'
    return pt_calib_vect, mass_calib_vect
