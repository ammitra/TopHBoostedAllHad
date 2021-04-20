import ROOT
ROOT.gROOT.SetBatch(True)

from THClass import THClass

selection = THClass('raw_nano/TprimeB-1200_16.txt',16)
selection.ApplyFlagsAndTrigs()
selection.ApplyKinematics()
selection.ApplyTopPick()
selection.ApplyStandardCorrections()
passfail = selection.ApplyHiggsTag()
selection.WrapUp(passfail.values())