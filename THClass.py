import ROOT
from TIMBER.Analyzer import Correction, ModuleWorker, analyzer
from TIMBER.Tools.Common import CompileCpp
from TIMBER.Tools.AutoPU import ApplyPU
from helpers import SplitUp
from JMEvalsOnly import JMEvalsOnly

class THClass:
    def __init__(self,inputfile,year,ijob,njobs):
        CompileCpp('THmodules.cc')
        infiles = SplitUp(inputfile, njobs)[ijob-1]
        self.a = analyzer(infiles)
        self.setname = inputfile.split('/')[-1].split('_')[0]
        self.year = year
        self.ijob = ijob
        self.njobs = njobs
        # self.dijetIdxs = [0,1]
        self.trigs = {
            16:[],
            17:[],
            18:[]
        }
        if 'Data' in self.setname:
            self.a.isData = True
        else:
            self.a.isData = False
    # def SetJetIdxs(self,idx0,idx1):
    #     self.dijetIdxs = [idx0,idx1]
    
    # def GetJetIdxTuple(self):
    #     return (self.dijetIdxs[0],self.dijetIdxs[1])

    def ApplyFlagsAndTrigs(self):
        self.a.Cut('flags',self.a.GetFlagString())
        # if self.a.isData: self.a.Cut('trigger',self.a.GetTriggerString(self.trigs[self.year]))

    def ApplyKinematics(self):
        self.a.Cut('njets','nFatJet > 2')
        self.a.Cut('pT', 'FatJet_pt[0] > 350 && FatJet_pt[1] > 350')
        self.a.Define('DijetIdxs','PickDijets(FatJet_pt, FatJet_eta, FatJet_phi, FatJet_msoftdrop)')
        self.a.Cut('dijetsExist','DijetIdxs[0] > -1 && DijetIdxs[1] > -1')
        self.a.SubCollection('Dijet','FatJet','DijetIdxs',useTake=True)
        self.a.Define('Dijet_vect','hardware::TLvector(Dijet_pt, Dijet_eta, Dijet_phi, Dijet_msoftdrop)')
        return self.a.GetActiveNode()

    def DefineTopIdx(self,tagger='deepTagMD_TvsQCD',invert=False):
        invertStr = 'Not' if invert else ''
        objIdxs = 'ObjIdxs_%s%s'%(invertStr,tagger)
        self.a.Define(objIdxs,'PickTop(Dijet_msoftdrop, Dijet_%s, {0, 1}, %s)'%(tagger,'true' if invert else 'false'))
        self.a.Define('tIdx','%s[0]'%objIdxs)
        self.a.Define('hIdx','%s[1]'%objIdxs)

    def ApplyTopPick(self,tagger='deepTagMD_TvsQCD',invert=False):
        objIdxs = 'ObjIdxs_%s%s'%('Not' if invert else '',tagger)
        if objIdxs not in [str(cname) for cname in self.a.DataFrame.GetColumnNames()]:
            self.DefineTopIdx(tagger,invert)
        self.a.Cut('HasTop','tIdx > -1')
        self.a.ObjectFromCollection('Top','Dijet','tIdx')
        self.a.ObjectFromCollection('Higgs','Dijet','hIdx')
        # self.c_top = Correction('TopTagSF','TIMBER/Framework/include/TopTagDAK8_SF.h',[self.year,'0p5',True],corrtype='weight')
        # self.a.AddCorrection(self.c_top, evalArgs={"pt":"Top_pt"})
        return self.a.GetActiveNode()
    
    def ApplyHiggsTag(self,tagger='deepTagMD_HbbvsQCD'):
        self.a.Define('mth','hardware::InvariantMass({Top_vect,Higgs_vect})')
        passfail = self.a.Discriminate('HbbTag','Higgs_%s > 0.9'%tagger)
        return passfail
        
    def ApplyStandardCorrections(self,snapshot=False):
        if snapshot:
            if self.a.isData:
                lumiFilter = ModuleWorker('LumiFilter','TIMBER/Framework/include/LumiFilter.h',[self.year])
                self.a.Cut('lumiFilter',lumiFilter.GetCall(evalArgs={"lumi":"luminosityBlock"}))
                if self.year == 18:
                    HEM_worker = ModuleWorker('HEM_drop','TIMBER/Framework/include/HEM_drop.h',[self.setname])
                    self.a.Cut('HEM','%s[0] > 0'%(HEM_worker.GetCall(evalArgs={"FatJet_eta":"Dijet_eta","FatJet_phi":"Dijet_phi"})))

            else:
                self.a = ApplyPU(self.a,'20%sUL'%self.year, 'THpileup.root', '%s_%s'%(self.setname,self.year))
                self.a.AddCorrection(
                    Correction('Pdfweight','TIMBER/Framework/include/PDFweight_uncert.h',[self.a.lhaid],corrtype='uncert')
                )
                if self.year == 16 or self.year == 17:
                    self.a.AddCorrection(
                        Correction("Prefire","TIMBER/Framework/include/Prefire_weight.h",[self.year],corrtype='weight')
                    )
                elif self.year == 18:
                    self.a.AddCorrection(
                        Correction('HEM_drop','TIMBER/Framework/include/HEM_drop.h',[self.setname],corrtype='corr')
                    )

                if 'ttbar' in self.a.fileName:
                    self.a.Define('GenPart_vect','hardware::TLvector(GenPart_pt, GenPart_eta, GenPart_phi, GenPart_mass)')
                    self.a.AddCorrection(
                        Correction('TptReweight','TIMBER/Framework/include/TopPt_weight.h',corrtype='weight'),
                        evalArgs={
                            "jet0":"Dijet_vect[0]",
                            "jet1":"Dijet_vect[1]"
                        }
                    )
            self.a = JMEvalsOnly(self.a, 'Dijet', str(2000+self.year), self.setname)
            self.a.MakeWeightCols()
        return self.a.GetActiveNode()

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
            'Dijet_eta','Dijet_msoftdrop','Dijet_pt','Dijet_phi',
            'Dijet_deepTagMD_HbbvsQCD', 'Dijet_deepTagMD_ZHbbvsQCD',
            'Dijet_deepTagMD_TvsQCD', 'Dijet_particleNet_HbbvsQCD',
            'Dijet_particleNet_TvsQCD', 'Dijet_rawFactor', 'Dijet_tau*',
            'Dijet_jetId', 'nFatJet', 'Dijet_JES_nom',
            'HLT_PFHT.*', 'HLT_PFJet.*', 'HLT_AK8.*',
            'event', 'eventWeight', 'luminosityBlock', 'run'
        ]

        if not self.a.isData:
            columns.extend(['GenPart_.*', 'nGenPart'])
            columns.extend(['Dijet_JES_up','Dijet_JES_down',
                            'Dijet_JER_nom','Dijet_JER_up','Dijet_JER_down',
                            'Dijet_JMS_nom','Dijet_JMS_up','Dijet_JMS_down',
                            'Dijet_JMR_nom','Dijet_JMR_up','Dijet_JMR_down'])
            columns.extend(['Pileup__nom','Pileup__up','Pileup__down','Pdfweight__nom','Pdfweight__up','Pdfweight__down'])
            if self.year == 16 or self.year == 17:
                columns.extend(['Prefire__nom','Prefire__up','Prefire__down'])
            elif self.year == 18:
                columns.append('HEM_drop__nom')

        node.Snapshot(columns,'THsnapshot_%s_%s_%sof%s.root'%(self.setname,self.year,self.ijob,self.njobs),'Events')