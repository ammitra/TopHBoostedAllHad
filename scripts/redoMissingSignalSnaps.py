from glob import glob

'''
Script to find out which signal files were not snapshotted
'''

raw = glob('raw_nano/Tprime*')
dijet = glob('dijet_nano/Tprime*')

dijet = [i.split('/')[-1].split('.')[0].split('_snapshot')[0] for i in dijet]

outSnap = open('missingSignalSnaps.txt','w')
outSel = open('missingSignalSelection.txt','w')

for r in raw:
    name_year = r.split('/')[-1].split('.')[0]
    if name_year not in dijet:
	#print(name_year)
	name = name_year.split('_')[0]
	year = name_year.split('_')[-1]
	outSnap.write('-s {} -y {} -j 1 -n 1\n'.format(name, year))
	outSel.write('-s {} -y {} -v None\n'.format(name,year))
	for syst in ['JES', 'JER', 'JMS', 'JMR', 'PNetTop', 'PNetXbb']:
	    for var in ['up', 'down']:
		outSel.write('-s {} -y {} -v {}_{} \n'.format(name, year, syst, var))

outSnap.close()
outSel.close()
