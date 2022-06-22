from TIMBER.Tools.Common import ExecuteCmd

def constantMT(mT):
    '''keep T' mass constant, vary the phi mass'''
    for mPhi in [75, 100, 125, 250, 500]:
        for year in ['16','16APV','17','18']:
            #ExecuteCmd('python THsnapshot.py -s TprimeB-{}-{} -y {}'.format(mT,mPhi,year))
	    print('-s TprimeB-{}-{} -y {}'.format(mT,mPhi,year))

def constantMPhi(mPhi):
    '''keep Phi mass constant, vary T' mass'''
    for mT in [14,15,16,17]:
	for year in ['16','16APV','17','18']:
	    #ExecuteCmd('python THsnapshot.py -s TprimeB-{}00-{} -y {}'.format(mT,mPhi,year))
	    print('-s TprimeB-{}00-{} -y {}'.format(mT,mPhi,year))

constantMT(1800)
constantMPhi(125)
