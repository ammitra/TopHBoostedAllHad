import ROOT
from TIMBER.Analyzer import Correction, CutGroup, ModuleWorker, analyzer
from TIMBER.Tools.Common import CompileCpp, OpenJSON
from TIMBER.Tools.AutoPU import ApplyPU
from helpers import SplitUp
import TIMBER.Tools.AutoJME as AutoJME

AutoJME.AK8collection = 'Dijet'

class THClass:
    def __init__(self,inputfile,year,ijob,njobs):
        if inputfile.endswith('.txt'): 
            infiles = SplitUp(inputfile, njobs)[ijob-1]
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
        self.year = str(year)	# most of the time this class will be instantiated from other scripts with CLI args, so just convert to string for internal use
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

        if 'Data' in inputfile:		# SingleMuonDataX_year and DataX_year are possible data inputfile names
            self.a.isData = True
        else:
            self.a.isData = False

    def AddCutflowColumn(self, var, varName):
	'''
	for future reference:
	https://root-forum.cern.ch/t/rdataframe-define-column-of-same-constant-value/34851
	'''
	print('Adding cutflow information...\n\t{}\t{}'.format(varName, var))
	self.a.Define('{}'.format(varName),str(var))
	

    def getNweighted(self):
	if not self.a.isData:
	    return self.a.DataFrame.Sum("genWeight").GetValue()
	else:
	    return self.a.DataFrame.Count().GetValue()

    ####################
    # Snapshot related #
    ####################
    def ApplyKinematicsSnap(self): # For snapshotting only
	# total number processed
	#self.NPROC = self.a.genEventSumw	# follow Matej https://github.com/mroguljic/X_YH_4b/blob/9602da767d1c1cf0e9fc19bade7b104b1da40212/eventSelection.py#L90
	self.NPROC = self.getNweighted()
	self.AddCutflowColumn(self.NPROC, "NPROC")

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
	MET_filters = self.a.GetFlagString(flags)	# string valid (existing in RDataFrame node) flags together w logical and
	self.a.Cut('flags', MET_filters)
	self.NFLAGS = self.getNweighted()
	self.AddCutflowColumn(self.NFLAGS, "NFLAGS")

        self.a.Cut('njets','nFatJet >= 2')
	self.NJETS = self.getNweighted()
	self.AddCutflowColumn(self.NJETS, "NJETS")

        # jetId cut: https://cms-pub-talk.web.cern.ch/t/jme-or/6547
        # INFO: https://twiki.cern.ch/twiki/bin/viewauth/CMS/JetID#nanoAOD_Flags
        self.a.Cut('jetId', 'Jet_jetId[0] > 1 && Jet_jetId[1] > 1')    # drop any events whose dijets did not both pass tight jetId requirement
        self.NJETID = self.getNweighted()
        self.AddCutflowColumn(self.NJETID, "NJETID")

        self.a.Cut('pT', 'FatJet_pt[0] > {0} && FatJet_pt[1] > {0}'.format(self.cuts['pt']))
	self.NPT = self.getNweighted()
	self.AddCutflowColumn(self.NPT, "NPT")

        self.a.Define('DijetIdxs','PickDijets(FatJet_pt, FatJet_eta, FatJet_phi, FatJet_msoftdrop)')
        self.a.Cut('dijetsExist','DijetIdxs[0] > -1 && DijetIdxs[1] > -1')
	self.NKIN = self.getNweighted()
	self.AddCutflowColumn(self.NKIN, "NKIN")

        self.a.SubCollection('Dijet','FatJet','DijetIdxs',useTake=True)
        self.a.Define('Dijet_vect','hardware::TLvector(Dijet_pt, Dijet_eta, Dijet_phi, Dijet_msoftdrop)')

	self.a.Define('deltaEta','abs(Dijet_eta[0]-Dijet_eta[1])')
	self.a.Cut('deltaEta_cut','deltaEta < 1.6')
	self.NDELTAETA = self.getNweighted()
	self.AddCutflowColumn(self.NDELTAETA,'NDELTAETA')
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
                self.a = ApplyPU(self.a, 'THpileup.root', self.year, ULflag=True, histname='{}_{}'.format(self.setname,self.year))
                self.a.AddCorrection(
                    Correction('Pdfweight','TIMBER/Framework/include/PDFweight_uncert.h',[self.a.lhaid],corrtype='uncert')
                )
                if self.year == '16' or self.year == '17' or self.year == '16APV':
		    # this is valid for calculating Prefire weights by TIMBER, but NanoAODv9 contains the weights as TLeafs in the Events TTree. So, let's just use that
		    '''
                    self.a.AddCorrection(
                        Correction("Prefire","TIMBER/Framework/include/Prefire_weight.h",[int(self.year) if 'APV' not in self.year else 16],corrtype='weight')
                    )
		    '''
		    # The column names are: L1PreFiringWeight_Up, L1PreFiringWeight_Dn, L1PreFiringWeight_Nom
		    L1PreFiringWeight = Correction("L1PreFiringWeight","TIMBER/Framework/TopPhi_modules/BranchCorrection.cc",constructor=[],mainFunc='evalWeight',corrtype='weight',columnList=['L1PreFiringWeight_Nom','L1PreFiringWeight_Up','L1PreFiringWeight_Dn'])
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
		self.a = AutoJME.AutoJME(self.a, 'Dijet', self.year, self.setname[10:])
	    else:
		# regardless of passing self.setname, the AutoJME function will check if input is data or not
		self.a = AutoJME.AutoJME(self.a, 'Dijet', self.year, self.setname)
            self.a.MakeWeightCols(extraNominal='genWeight' if not self.a.isData else '')
        
        else:
            if not self.a.isData:
                self.a.AddCorrection(Correction('Pileup',corrtype='weight'))
                self.a.AddCorrection(Correction('Pdfweight',corrtype='uncert'))
                if self.year == '16' or self.year == '17' or self.year == '16APV':
                    #self.a.AddCorrection(Correction('Prefire',corrtype='weight'))
		    self.a.AddCorrection(Correction('L1PreFiringWeight',corrtype='weight'))
                elif self.year == '18':
                    self.a.AddCorrection(Correction('HEM_drop',corrtype='corr'))
                if 'ttbar' in self.setname:
                    self.a.AddCorrection(Correction('TptReweight',corrtype='weight'))
                
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
	self.AddCutflowColumn(self.PreLeptonVeto,'PreLepVeto')
	# tightMu inversion
	self.a.Cut('tightMu_veto','TightMuVeto(nMuon, Muon_tightId, Muon_pt, Muon_pfRelIso04_all, Muon_eta)==0')
	self.NTightMu = self.getNweighted()
	self.AddCutflowColumn(self.NTightMu, "NTightMu")
	# tightEl inversion
	self.a.Cut('tightEl_veto','TightElVeto(nElectron, Electron_mvaFall17V2Iso_WP80, Electron_pt, Electron_eta)==0')
	self.NTightEl = self.getNweighted()
	self.AddCutflowColumn(self.NTightEl, "NTightEl")
	# goodMu inversion
	self.a.Cut('goodMu_veto','GoodMuVeto(nMuon, Muon_pt, Muon_looseId, Muon_dxy, Muon_eta)==0')
	self.NGoodMu = self.getNweighted()
	self.AddCutflowColumn(self.NGoodMu, "NGoodMu")
	# goodEl inversion
	self.a.Cut('goodEl_veto','GoodElVeto(nElectron, Electron_pt, Electron_mvaFall17V2noIso_WP90, Electron_dxy, Electron_eta)==0')
	self.NGoodEl = self.getNweighted()
	self.AddCutflowColumn(self.NGoodEl, "NGoodEl")

	self.PostLeptonVeto = self.getNweighted()
	self.AddCutflowColumn(self.PostLeptonVeto,'PostLepVeto')
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
	    'NPROC', 'NFLAGS', 'NJETID', 'NJETS', 'NPT', 'NKIN', 'NDELTAETA', 'NTightMu', 'NTightEl', 'NGoodMu', 'NGoodEl', 'PreLepVeto', 'PostLepVeto'
        ]

        if not self.a.isData:
            columns.extend(['GenPart_.*', 'nGenPart','genWeight'])
            columns.extend(['Dijet_JES_up','Dijet_JES_down',
                            'Dijet_JER_nom','Dijet_JER_up','Dijet_JER_down',
                            'Dijet_JMS_nom','Dijet_JMS_up','Dijet_JMS_down',
                            'Dijet_JMR_nom','Dijet_JMR_up','Dijet_JMR_down'])
            columns.extend(['Pileup__nom','Pileup__up','Pileup__down','Pdfweight__nom','Pdfweight__up','Pdfweight__down'])
            if self.year == '16' or self.year == '17' or self.year == '16APV':
                #columns.extend(['Prefire__nom','Prefire__up','Prefire__down'])					# these are the TIMBER prefire calculations (don't include)
		columns.extend(['L1PreFiringWeight_Nom', 'L1PreFiringWeight_Up', 'L1PreFiringWeight_Dn'])	# keep the TIMBER Prefire calculations, but also include these from NanoAODv9
		columns.extend(['L1PreFiringWeight__nom','L1PreFiringWeight__up','L1PreFiringWeight__down'])    # these are the weight columns created by the BranchCorrection module 
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
	#########################################################################################
	# This is *not* a viable description of HT
	# need to fix
	#########################################################################################
        # for trigger studies
        self.a.Define('pt0','Dijet_pt_corr[0]')
        self.a.Define('pt1','Dijet_pt_corr[1]')
        self.a.Define('HT','pt0+pt1')
        return self.a.GetActiveNode()

    def ApplyTopPick_Signal(self, TopTagger, XbbTagger, pt, mass, TopScoreCut, eff0, eff1, year, TopVariation, invert, ttbarCR=False):
	objIdxs = 'ObjIdxs{}_{}{}'.format('_ttbarCR' if ttbarCR else '', 'Not' if invert else '', TopTagger)
	if objIdxs not in [str(cname) for cname in self.a.DataFrame.GetColumnNames()]:
	    self.a.Define(objIdxs, 'PickTopWithSFs(%s, %s, %s, %s, {0, 1}, %f, %f, %f, "20%s", %i, %s)'%(TopTagger, XbbTagger, pt, mass, TopScoreCut, eff0, eff1, year, TopVariation, 'true' if invert else 'false'))
	    # at this point, we'll have a column named ObjIdxs_(NOT)_particleNet_TvsQCD contianing the indices of which of the two jets is the top and the phi (top-0, Phi-1)
	    # or, if neither passed it will look like {-1,-1}
	    self.a.Define('tIdx','{}[0]'.format(objIdxs))
	    self.a.Define('hIdx','{}[1]'.format(objIdxs))
	#DEBUG
	nTot = self.a.DataFrame.Sum("genWeight").GetValue()
	print('NTot before TopPick (signal) = {}'.format(nTot))
	self.a.Cut('HasTop','tIdx > -1')
        #DEBUG
        nTot = self.a.DataFrame.Sum("genWeight").GetValue()
        print('NTot after TopPick (signal) = {}'.format(nTot))

        # now get the cutflow information after top tag
        if (invert == True):    # control region
            self.nTop_CR = self.getNweighted()
            self.AddCutflowColumn(self.nTop_CR, "nTop_CR")
        else:
            self.nTop_SR = self.getNweighted()
            self.AddCutflowColumn(self.nTop_SR, "nTop_SR")

        # at this point, rename Dijet -> Top/Higgs based on its index determined above
        self.a.ObjectFromCollection('Top','Dijet','tIdx',skip=['msoftdrop_corrH'])
        self.a.ObjectFromCollection('Higgs','Dijet','hIdx',skip=['msoftdrop_corrT'])
        self.a.Define('Top_vect','hardware::TLvector(Top_pt_corr, Top_eta, Top_phi, Top_msoftdrop_corrT)')
        self.a.Define('Higgs_vect','hardware::TLvector(Higgs_pt_corr, Higgs_eta, Higgs_phi, Higgs_msoftdrop_corrH)')
        self.a.Define('mth','hardware::InvariantMass({Top_vect,Higgs_vect})')
        return self.a.GetActiveNode()	


    def ApplyTopPick(self,tagger='deepTag_TvsQCD',invert=False, CRv2=None, ttbarCR=False):
        objIdxs = 'ObjIdxs%s_%s%s'%('_ttbarCR' if ttbarCR else '','Not' if invert else '',tagger)
        if objIdxs not in [str(cname) for cname in self.a.DataFrame.GetColumnNames()]:

	    if (CRv2 == None):
		# perform the CR_v1 top pick (DEPRECATED)
                self.a.Define(objIdxs,'PickTop(Dijet_msoftdrop_corrT, Dijet_%s, {0, 1}, {%s,%s}, %s, %s)'%(tagger, self.cuts['mt'][0], self.cuts['mt'][1], self.cuts[tagger], 'true' if invert else 'false'))
	    else:
		# perform the CR_v2 top pick 
		self.a.Define(objIdxs,'PickTopCRv2(Dijet_msoftdrop_corrT, Dijet_%s, Dijet_%s, {0, 1}, {%s,%s}, %s, %s)'%(tagger, CRv2, self.cuts['mt'][0], self.cuts['mt'][1], self.cuts[tagger], 'true' if invert else 'false'))

	    # at this point, we'll have a column named ObjIdxs_(NOT)_particleNet_TvsQCD containing the indices of which of the two jets is the top and Higgs (top-0, Higgs-1)
	    # or, if neither passed, it will look like {-1, -1}
            self.a.Define('tIdx','%s[0]'%objIdxs)	# the first object in the resulting collection is the top
            self.a.Define('hIdx','%s[1]'%objIdxs)	# the second is the Higgs
        self.a.Cut('HasTop','tIdx > -1')		# now we cut on all jets that *have* a top candidate (PickTop() returns {-1, -1} if neither jet passes)
	
	# now get the cutflow information after top tag
	if (invert == True):	# control region
	    self.nTop_CR = self.getNweighted()
	    self.AddCutflowColumn(self.nTop_CR, "nTop_CR")
	else:
	    self.nTop_SR = self.getNweighted()
	    self.AddCutflowColumn(self.nTop_SR, "nTop_SR")

	# at this point, rename Dijet -> Top/Higgs based on its index determined above
        self.a.ObjectFromCollection('Top','Dijet','tIdx',skip=['msoftdrop_corrH'])
        self.a.ObjectFromCollection('Higgs','Dijet','hIdx',skip=['msoftdrop_corrT'])
        self.a.Define('Top_vect','hardware::TLvector(Top_pt_corr, Top_eta, Top_phi, Top_msoftdrop_corrT)')
        self.a.Define('Higgs_vect','hardware::TLvector(Higgs_pt_corr, Higgs_eta, Higgs_phi, Higgs_msoftdrop_corrH)')
        self.a.Define('mth','hardware::InvariantMass({Top_vect,Higgs_vect})')
        return self.a.GetActiveNode()

    def ApplyNewTrigs(self, subyear, corr=None):
	'''
	for use with the new triggers, using the triggers listed in THconfig.json, derived via scripts/trigTest.py
	subyear str = name of subyear file in dijet_nano, e.g. "DataC_17"
	'''
	if self.a.isData:
	    subyearTrigs = self.newTrigs[subyear]
	    # due to Python JSON weirdness, the above list will have all elements in unicode, so need to convert to ascii
	    trigs = [trig.encode('ascii','ignore') for trig in subyearTrigs]
	    self.a.Cut('trigger', self.a.GetTriggerString(trigs))
	else:
	    self.a.AddCorrection(corr, evalArgs={"xval":"m_javg","yval":"mth_trig"})
	return self.a.GetActiveNode()

    def ApplyTrigs(self,corr=None):
        if self.a.isData:
            self.a.Cut('trigger',self.a.GetTriggerString(self.trigs[int(self.year) if 'APV' not in self.year else 16]))
        else:
            self.a.AddCorrection(corr, evalArgs={"xval":"m_javg","yval":"mth_trig"})    
        return self.a.GetActiveNode()

    def ApplyTopTag_ttbarCR(self, tagger='deepTagMD_HbbvsQCD', topTagger='deepTagMD_TvsQCD', signal=False, loose=True):
	'''
	Used to create the Fail and Pass regions of the ttbar control region. 
	The ttbar CR Fail is defined identically to the SR fail, that is, one jet PNet top-tagged and the other jet failing an Hbb score. 
	The ttbar CR Pass region is then defined by one jet PNet top-tagged and the other jet passing the deepAK8 MD top tagging.
	WPs: https://twiki.cern.ch/twiki/bin/view/CMS/DeepAK8Tagging2018WPsSFs#Working_Points
	'''
	# 0.5% WP = loose, 0.1% = tight
	if ('16' in self.year):
	    WP = 0.632 if loose else 0.889
	elif (self.year == '17'):
	    WP = 0.554 if loose else 0.863
	else:
	    WP = 0.685 if loose else 0.92
	checkpoint = self.a.GetActiveNode()
	passFail = {}
	# for the ttbar CR, we start same as SR fail. Then we want to operate on the Hbb candidate jet, since we've already ID'd the top
	passFail['SRfail'] = self.a.Cut('ttbarCR_Hbb_fail','Higgs_{0} < 0.8'.format(tagger) if not signal else 'NewTagCats==0')
	# the Fail region is then a failing deepAK8 tagger 
	passFail['fail'] = self.a.Cut('ttbarCR_top_fail','Higgs_{0} < {1}'.format(topTagger,WP))
	self.a.SetActiveNode(checkpoint)
	# the Pass region is then a deepAK8 MD top tagger > some working point 
	passFail['pass'] = self.a.Cut('ttbarCR_top_pass','Higgs_{0} > {1}'.format(topTagger,WP))
	# reset active node, return dict
	self.a.SetActiveNode(checkpoint)
	return passFail


    def ApplyHiggsTag(self, SRorCR, tagger='deepTagMD_HbbvsQCD', signal=False):
	'''
	    SRorCR [str] = "SR" or "CR" - used to generate cutflow information after each Higgs tagger cut
	    tagger [str] = discriminator used for Higgs ID. default: particleNetMD_HbbvsQCD
		NOTE: The ApplyTopPick() function will create a column with the name Higgs_particleNetMD_HbbvsQCD, so we have to select for that below
	    signal [bool] = whether signal or not. If signal, then perform Higgs tag based on columns created after SF application:
		Pass:   NewTagCats==2		# see ParticleNet_SF.cc and THselection.py for more information
		Loose:  NewTagCats==1
		Fail:   NewTagCats==0
	'''
	assert(SRorCR == 'SR' or SRorCR == 'CR')
        checkpoint = self.a.GetActiveNode()
        passLooseFail = {}
	# Higgs Pass + cutflow info
        passLooseFail["pass"] = self.a.Cut('HbbTag_pass','Higgs_{0} > {1}'.format(tagger,self.cuts[tagger]) if not signal else 'NewTagCats==2')
	if SRorCR == 'SR':
	    self.higgsP_SR = self.getNweighted()
	    self.AddCutflowColumn(self.higgsP_SR, "higgsP_SR")
	else:
	    self.higgsP_CR = self.getNweighted()
	    self.AddCutflowColumn(self.higgsP_CR, "higgsP_CR")
	# Higgs Loose + cutflow info
        self.a.SetActiveNode(checkpoint)
        passLooseFail["loose"] = self.a.Cut('HbbTag_loose','Higgs_{0} > 0.8 && Higgs_{0} < {1}'.format(tagger,self.cuts[tagger]) if not signal else 'NewTagCats==1')
        if SRorCR == 'SR':
            self.higgsL_SR = self.getNweighted()
	    self.AddCutflowColumn(self.higgsL_SR, "higgsL_SR")
        else:
            self.higgsL_CR = self.getNweighted()
	    self.AddCutflowColumn(self.higgsL_CR, "higgsL_CR")
	# Higgs Fail + cutflow info
        self.a.SetActiveNode(checkpoint)
        passLooseFail["fail"] = self.a.Cut('HbbTag_fail','Higgs_{0} < 0.8'.format(tagger,self.cuts[tagger]) if not signal else 'NewTagCats==0')
        if SRorCR == 'SR':
            self.higgsF_SR = self.getNweighted()
	    self.AddCutflowColumn(self.higgsF_SR, "higgsF_SR")
        else:
            self.higgsF_CR = self.getNweighted()
	    self.AddCutflowColumn(self.higgsF_CR, "higgsF_CR")
	# reset node state, return dict
        self.a.SetActiveNode(checkpoint)
        return passLooseFail
        
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

    def GetXsecScale(self):
        lumi = self.config['lumi{}'.format(self.year if 'APV' not in self.year else 16)]
        xsec = self.config['XSECS'][self.setname]
        if self.a.genEventSumw == 0:
            raise ValueError('%s %s: genEventSumw is 0'%(self.setname, self.year))
        return lumi*xsec/self.a.genEventSumw

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
