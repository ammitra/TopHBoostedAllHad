import glob
import ROOT
from THClass import THClass

'''
Test for determining which trigger columns the subyears have
'''

dataFiles = glob.glob("../dijet_nano/Data*.txt")

trigs = {
    16:['HLT_PFHT800','HLT_PFHT650_WideJetMJJ900DEtaJJ1p5','HLT_PFHT900','HLT_AK8PFJet450'],
    17:['HLT_PFHT1050','HLT_AK8PFJet500','HLT_AK8PFHT750_TrimMass50','HLT_AK8PFHT800_TrimMass50','HLT_AK8PFJet400_TrimMass30'],
    18:['HLT_PFHT1050','HLT_AK8PFHT800_TrimMass50','HLT_AK8PFJet500','HLT_AK8PFJet400_TrimMass30']
}

out = {}
length = len(dataFiles) - 4	# subtract the concatendated data files
count = 0	# keep track of how many we're investigating, just to make sure all accounted for

for f in dataFiles:
    if "Data_" in f:	# skip  the concatenated data files, we need to look per subyear
	continue
    count += 1
    print('Opening {}'.format(f))
    year = f.split("/")[1].split("_")[1]
    name = f.split("/")[1].split("_")[0] + '_' + year
    sel = THClass(f,year,1,1)
    available_trigs = sel.a.GetTriggerString(trigs[int(year) if 'APV' not in year else 16])
    out[name] = available_trigs

assert(length==count)

for name, trigs in out.items():
    print('------------------------------------------------')
    print('{} : {}'.format(name, trigs))
    print('------------------------------------------------')
