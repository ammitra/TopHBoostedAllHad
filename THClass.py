import ROOT
from TIMBER.Analyzer import Correction, ModuleWorker, analyzer
from TIMBER.Tools.Common import CompileCpp
from TIMBER.Tools.AutoPU import AutoPU
from helpers import SplitUp

class THClass:
    def __init__(self,inputfile,year,ijob,njobs):
        CompileCpp('THmodules.cc')
        infiles = SplitUp(inputfile, njobs)[ijob-1]
        self.a = analyzer(infiles)
        self.setname = inputfile.split('/')[-1].split('_')[0]
        self.year = year
        self.ijob = ijob
        self.njobs = njobs
        self.dijetIdxs = [0,1]
        self.trigs = {
            16:[],
            17:[],
            18:[]
        }

        self.ApplyFlagsAndTrigs()
        
    def SetJetIdxs(self,idx0,idx1):
        self.dijetIdxs = [idx0,idx1]
    
    def GetJetIdxTuple(self):
        return (self.dijetIdxs[0],self.dijetIdxs[1])

    def ApplyFlagsAndTrigs(self):
        self.a.Cut('flags',self.a.GetFlagString())
        # if self.a.isData: self.a.Cut('trigger',self.a.GetTriggerString(self.trigs[self.year]))

    def ApplyKinematics(self):
        self.a.Cut('njets','nFatJet > max(%s,%s)'%self.GetJetIdxTuple())
        self.a.Cut('pT','FatJet_pt[%s] > 350 && FatJet_pt[%s] > 350'%self.GetJetIdxTuple())
        self.a.Cut('eta','abs(FatJet_eta[%s]) < 2.4 && abs(FatJet_eta[%s]) < 2.4'%self.GetJetIdxTuple())
        self.a.Cut('deltaPhi','hardware::DeltaPhi(FatJet_phi[%s],FatJet_phi[%s]) > M_PI/2'%self.GetJetIdxTuple())
        return self.a.GetActiveNode()

    def ApplyTopPick(self):
        self.a.Define('jetIdxs','PickTop(FatJet_msoftdrop, FatJet_deepTag_TvsQCD, {%s, %s})'%self.GetJetIdxTuple())
        self.a.Define('tIdx','jetIdxs[0]')
        self.a.Define('hIdx','jetIdxs[1]')
        self.a.Cut('HasTop','tIdx > -1')

        self.a.ObjectFromCollection('Top','FatJet','tIdx')
        self.a.Define('Top_vect','hardware::TLvector(Top_pt,Top_eta,Top_phi,Top_msoftdrop)')
        
        self.a.ObjectFromCollection('Higgs','FatJet','hIdx')
        self.a.Define('Higgs_vect','hardware::TLvector(Higgs_pt,Higgs_eta,Higgs_phi,Higgs_msoftdrop)')
        
        # self.c_top = Correction('TopTagSF','TIMBER/Framework/include/TopTagDAK8_SF.h',[self.year,'0p5',True],corrtype='weight')
        # self.a.AddCorrection(self.c_top, evalArgs={"pt":"Top_pt"})
        return self.a.GetActiveNode()

    def ApplyStandardCorrections(self,snapshot=False):
        if self.a.isData:
            lumiFilter = ModuleWorker('LumiFilter','TIMBER/Framework/include/LumiFilter.h',[self.year])
            self.a.Cut('lumiFilter',lumiFilter.GetCall(inArgs={"lumi":"luminosityBlock"}))
            if self.year == 18:
                HEM_worker = ModuleWorker('HEM_drop','TIMBER/Framework/include/HEM_drop.h',[self.setname,'{%s,%s}'%self.GetJetIdxTuple()])
                self.a.Cut('HEM','%s[0] > 0'%(HEM_worker.GetCall()))

        else:
            self.a = AutoPU(self.a, '20%sUL'%self.year)
            self.a.AddCorrection(
                Correction('Pdfweight','TIMBER/Framework/include/PDFweight_uncert.h',[self.a.lhaid],corrtype='uncert')
            )
            if self.year == 16 or self.year == 17:
                self.a.AddCorrection(
                    Correction("Prefire","TIMBER/Framework/include/Prefire_weight.h",[self.year],corrtype='weight')
                )
            elif self.year == 18:
                self.a.AddCorrection(
                    Correction('HEM_drop','TIMBER/Framework/include/HEM_drop.h',[self.setname,'{%s,%s}'%self.GetJetIdxTuple()],corrtype='corr')
                )

            if 'ttbar' in self.a.fileName and not snapshot:
                self.a.Define('GenPart_vect','hardware::TLvector(GenPart_pt, GenPart_eta, GenPart_phi, GenPart_mass')
                self.a.AddCorrection(
                    Correction('TptReweight','TIMBER/Framework/include/TopPt_weight.h',corrtype='weight'),
                    evalArgs={
                        "jet0":"Top_vect"%self.dijetIdxs[0],
                        "jet":"Higgs_vect"%self.dijetIdxs[1]}
                )
        if not snapshot: self.a.MakeWeightCols()
        
        return self.a.GetActiveNode()

    def ApplyHiggsTag(self):
        self.a.Define('mth','hardware::InvariantMass({Top_vect,Higgs_vect})')
        passfail = self.a.Discriminate('HbbTag','Higgs_deepTagMD_HbbvsQCD > 0.9')
        return passfail
        
    def WrapUp(self,nodes):
        outfile = ROOT.TFile.Open(self.a.fileName.replace('.txt','.root'),'RECREATE')
        for n in nodes:
            self.a.SetActiveNode(n)
            templates = self.a.MakeTemplateHistos(ROOT.TH2F('MthvMh','MthvMh',40,60,260,28,800,2200),['Higgs_msoftdrop','mth'])
            outfile.cd()
            templates.Do('Write')
            # self.a.DrawTemplates(templates,'plots/')

        outfile.Close()

    def Snapshot(self,node=None):
        if node == None: node = self.a.GetActiveNode()

        columns = [
            'FatJet_eta','FatJet_msoftdrop','FatJet_pt','FatJet_phi',
            'FatJet_deepTagMD_HbbvsQCD', 'FatJet_deepTagMD_ZHbbvsQCD',
            'FatJet_deepTagMD_TvsQCD', 'FatJet_particleNet_HbbvsQCD',
            'FatJet_particleNet_TvsQCD', 'FatJet_rawFactor', 'FatJet_tau*',
            'FatJet_jetId', 'nFatJet',
            'HLT_PFHT.*', 'HLT_PFJet.*', 'HLT_AK8.*',
            'event', 'eventWeight', 'luminosityBlock', 'run'
        ]

        if not self.a.isData:
            columns.extend(['GenPart_.*', 'nGenPart',])
            columns.extend(['pileup__nom','pileup__up','pileup__down','Pdfweight__nom','Pdfweight__up','Pdfweight__down'])
            if self.year == 16 or self.year == 17:
                columns.append(['Prefire__nom','Prefire__up','Prefire__down'])
            elif self.year == 18:
                columns.append('HEM_drop__nom')

        node.Snapshot(columns,'THsnapshot_%s_%s_%sof%s.root'%(self.setname,self.year,self.ijob,self.njobs),'Events')