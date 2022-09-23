import ROOT
from TIMBER.Analyzer import analyzer

'''
small script to determine the fraction of data in the 2017 dataset belonging to Run 2017B.

The full 2017 dataset consists of eras B, C, D, E, and F, but run B lacks substructure- and grooming-based triggers and so is dropped from the dataset. The efficiency for run B is still calculated and saved in THtrigger_17B.root and THtrigger2D_17B.root, and must be applied to a fraction of 2017 MC equal to the contribution of 2017B to the full 2017 dataset
'''

# we will compare the number of events in both the SingleMuon and JetHT datasets after preselection

#-------------------------------------------------------------
#		JetJT
#-------------------------------------------------------------
JetHT_full = analyzer('dijet_nano/DataWithB_17_snapshot.txt')
JetHT_den = float(JetHT_full.DataFrame.Count().GetValue())
JetHT_full.Close()
JetHT_later = analyzer('dijet_nano/Data_17_snapshot.txt')
JetHT_num = float(JetHT_later.DataFrame.Count().GetValue())
JetHT_later.Close()
#-------------------------------------------------------------
#               SingleMuon
#-------------------------------------------------------------
SingleMuon_full = analyzer('dijet_nano/SingleMuonDataWithB_17_snapshot.txt')
SingleMuon_den = float(SingleMuon_full.DataFrame.Count().GetValue())
SingleMuon_full.Close()
SingleMuon_later = analyzer('dijet_nano/SingleMuonData_17_snapshot.txt')
SingleMuon_num = float(SingleMuon_later.DataFrame.Count().GetValue())
SingleMuon_later.Close()

# now calculate ratio 
print('Later  JetHT:  	 {}'.format(JetHT_num))
print('Full JetHT:      {}'.format(JetHT_den))
print('Later SingleMuon:  {}'.format(SingleMuon_num))
print('Full SingleMuon: {}'.format(SingleMuon_den))

JetHT_ratio = JetHT_num/JetHT_den
SingleMuon_ratio = SingleMuon_num/SingleMuon_den
print('JetHT full/later =      {}'.format(JetHT_ratio))
print('SingleMuon full/later = {}'.format(SingleMuon_ratio))


print('-------------------------------------------------------------------')
print('Run 2017B makes up {}% of the 2017 JetHT dataset'.format((1.-JetHT_ratio)*100.))
print('Run 2017B makes up {}% of the 2017 SingleMuon dataset'.format((1.-SingleMuon_ratio)*100.))



