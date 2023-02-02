'''
Gathers all rootfiles from the EOS and dumps it into the rootfiles/ directory 
'''
from glob import glob
import subprocess, os
from TIMBER.Tools.Common import ExecuteCmd
import ROOT

def GetAllFiles():
    return [f for f in glob('dijet_nano/*_snapshot.txt') if f != '']
def GetProcYearFromTxt(filename):
    pieces = filename.split('/')[-1].split('.')[0].split('_')
    if '.txt' in filename:
        return pieces[0], pieces[1]
    elif '.root' in filename:
        return pieces[1], pieces[2]
    else:
	print('ERROR')

def CombineCommonSets(groupname,doStudies=False,modstr='',HT=''):
    '''Which stitch together either QCD or ttbar (ttbar-allhad+ttbar-semilep)
    @param groupname (str, optional): "QCD" or "ttbar".
    '''

    if groupname not in ["QCD","ttbar","W","Z"]:
        raise ValueError('Can only combine QCD or ttbar or W/Z')
    
    for y in ['16','16APV','17','18']:
        baseStr = 'rootfiles/TH%s_HT%s_{0}{2}_{1}{3}.root'%(HT,'studies' if doStudies else 'selection')
        if groupname == 'ttbar':
            to_loop = [''] if doStudies else ['','JES','JER','JMS','JMR']
            for v in to_loop:
                if v == '':
                    ExecuteCmd('hadd -f -k %s %s %s'%(
                        baseStr.format('ttbar',y,modstr,''),
                        baseStr.format('ttbar-allhad',y,modstr,''),
                        baseStr.format('ttbar-semilep',y,modstr,''))
                    )
                else:
                    for v2 in ['up','down']:
                        v3 = '_%s_%s'%(v,v2)
                        ExecuteCmd('hadd -f -k %s %s %s'%(
                            baseStr.format('ttbar',y,modstr,v3),
                            baseStr.format('ttbar-allhad',y,modstr,v3),
                            baseStr.format('ttbar-semilep',y,modstr,v3))
                        )
        elif groupname == 'QCD':
            ExecuteCmd('hadd -f -k %s %s %s %s %s'%(
                baseStr.format('QCD',y,modstr,''),
                baseStr.format('QCDHT700',y,modstr,''),
                baseStr.format('QCDHT1000',y,modstr,''),
                baseStr.format('QCDHT1500',y,modstr,''),
                baseStr.format('QCDHT2000',y,modstr,''))
            )

        elif groupname == 'W' or 'Z':
            to_loop = [''] if doStudies else ['','JES','JER','JMS','JMR']
            for v in to_loop:
                if v == '':
                    ExecuteCmd('hadd -f -k %s %s %s %s'%(
                        baseStr.format('{}Jets'.format('W' if groupname == 'W' else 'Z'),y,modstr,''),
                        baseStr.format('{}JetsHT400'.format('W' if groupname == 'W' else 'Z'),y,modstr,''),
                        baseStr.format('{}JetsHT600'.format('W' if groupname == 'W' else 'Z'),y,modstr,''),
                        baseStr.format('{}JetsHT800'.format('W' if groupname == 'W' else 'Z'),y,modstr,''))
                    )
                else:
                    for v2 in ['up','down']:
                        v3 = '_{}_{}'.format(v,v2)
                        ExecuteCmd('hadd -f -k %s %s %s %s'%(
                            baseStr.format('{}Jets'.format('W' if groupname == 'W' else 'Z'),y,modstr,v3),
                            baseStr.format('{}JetsHT400'.format('W' if groupname == 'W' else 'Z'),y,modstr,v3),
                            baseStr.format('{}JetsHT600'.format('W' if groupname == 'W' else 'Z'),y,modstr,v3),
                            baseStr.format('{}JetsHT800'.format('W' if groupname == 'W' else 'Z'),y,modstr,v3))
                        )

def MakeRun2(setname,doStudies=False,modstr='',HT=''):
    t = 'studies' if doStudies else 'selection'
    ExecuteCmd('hadd -f -k rootfiles/TH{1}_HT{3}_{0}{2}_Run2.root rootfiles/TH{1}_{0}{2}_16.root rootfiles/TH{1}_{0}{2}_17.root rootfiles/TH{1}_{0}{2}_18.root'.format(setname,t,modstr,HT))


# ------------------------------------------------------------------------------------------
if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--HT', type=str, dest='HT',
			action='store', default='0',
			 help='Value of HT to cut on')
    args = parser.parse_args()

    redirector = 'root://cmseos.fnal.gov/'
    eos_path = '/store/user/ammitra/topHBoostedAllHad/selection/THselection_HT{}*'.format(args.HT)

    rawFiles = subprocess.check_output('eos {} ls {}'.format(redirector,eos_path), shell=True)
    files = rawFiles.split('\n')

    for fName in files:
	if (fName == '') or ('Muon' in fName):
	    pass
    	else:
            ExecuteCmd('xrdcp {}{}{} rootfiles/'.format(redirector, eos_path, fName))

    # now that we have all files, perform housekeeping
    CombineCommonSets('QCD', False, args.HT)
    CombineCommonSets('ttbar', False, args.HT)
    CombineCommonSets('W', False, args.HT)
    CombineCommonSets('Z', False, args.HT)
    MakeRun2('Data', False, args.HT)

