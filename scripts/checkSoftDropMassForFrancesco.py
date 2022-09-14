# for Francesco, comparing the softdrop mass corrections b/w JER down and up

import ROOT, time
from collections import OrderedDict
from TIMBER.Analyzer import HistGroup, Correction
from TIMBER.Tools.Common import CompileCpp
ROOT.gROOT.SetBatch(True)
from THClass import THClass

#trigEff = Correction("TriggerEff18",'TIMBER/Framework/include/EffLoader.h',['THtrigger2D_18.root','Pretag'], corrtype='weight')

for var in ['None','JER_up','JER_down']:
    print('performing {} variation'.format(var))
    selection = THClass('dijet_nano/QCDHT1500_17_snapshot.txt','17',1,1)
    selection.OpenForSelection(var)
    #selection.ApplyTrigs(trigEff)
    selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())
    selection.a.Snapshot(['Dijet_msoftdrop_corrT', 'Dijet_msoftdrop_corrH'], "checkSDmass_{}.root".format(var),'m_sd',openOption='RECREATE')
    
