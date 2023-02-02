sampleFile = open('../condor/highMassTprime_pileup_args.txt','r')
outFile = open('../condor/highMassTprime_selection_args.txt','w')

lines = sampleFile.readlines()
for line in lines:
    signal = line.strip()
    signalNone = signal + ' -v None\n'
    outFile.write(signalNone)
    for jec in ['JMS','JMR','JES','JER','PNetXbb','PNetTop']:
	for var in ['up','down']:
	    signalJEC = signal + ' -v {}_{}\n'.format(jec,var)
	    outFile.write(signalJEC)

outFile.close()

