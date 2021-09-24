import json
from TIMBER.Tools.Common import OpenJSON, DictCopy

def polyStrGen(xorder,yorder):
    xparts = ['@0']
    yparts = ['1']
    totalParams = 0
    for i in range(1,xorder+1):
        xparts.append('@{0}*x**{1}'.format(totalParams,i))
        totalParams += 1
    for i in range(1,yorder+1):
        yparts.append('@{0}*y**{1}'.format(totalParams,i))
        totalParams += 1
    return 'max(0,0.1*(%s)*(%s))'%('+'.join(xparts),'+'.join(yparts)),totalParams

template = OpenJSON('template.json')
parameterDict = {
    "NOMINAL": 0.1,
    "MIN":-10.0,
    "MAX":10.0,
    "ERROR":0.05
}
parameterDict0 = DictCopy(parameterDict)
parameterDict0['MIN'] = -10.0

shortNames = {
    'deepTag':'DAK8',
    'particleNet':'PN'
}

for tagger in ['deepTag','particleNet']:
    for xorder in range(3):
        for yorder in range(3):
            outDict = DictCopy(template)
            outDict['GLOBAL']['baseName'] = 'MthvMh_'+tagger
            outDict['FIT']['FORM'],nparams = polyStrGen(xorder,yorder)
            for i in range(nparams):
                if i == 0:
                    outDict['FIT'][str(i)] = parameterDict0
                else:
                    outDict['FIT'][str(i)] = parameterDict

            with open('input_dataTpBlindedRun2_%s_%sx%s.json'%(shortNames[tagger],xorder,yorder),'w') as outfile:
                json.dump(outDict,outfile,indent=4, separators=(',', ': '))

