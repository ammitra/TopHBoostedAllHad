'''Script to ensure that the combination of data works as expected'''
from collections import Counter
import glob
import subprocess
import ROOT

def check_subs(inFile, year):
    f = open(inFile)
    lines = [i.strip() for i in f.readlines()]
    eras = {}
    for line in lines:
	fname = line.split('/')[-1].split('.')[0]
	yr = fname.split('_')[2]
	assert(yr==year)
	era = fname.split('_')[1]
	if era in eras: continue
	amount = fname.split('of')[-1]
	eras[era] = amount
    for era in eras.keys():
	total = subprocess.check_output('cat {} | grep {} | wc -l'.format(inFile,era),shell=True)
	print('%s_%s:'%(era,yr))
	if int(total) == int(eras[era]):
	    print('\t OK: {}/{}'.format(int(total),int(amount)))
	else:
	    print('\t ERROR ------------------------')
	    print('\t {}/{}'.format(int(total),int(amount)))

print('Checking whether dijet_nano snapshots for selection are correct:')
files = subprocess.check_output('ls dijet_nano/ | grep Data | grep -v Muon',shell=True).split('\n')
for f in files:
    if 'Data' not in f: continue
    check_subs('dijet_nano/%s'%f, f.split('_')[1])

b_run2 = ROOT.TFile.Open('root://cmseosmgm01.fnal.gov:1094//store/user/ammitra/topHBoostedAllHad/selection_backup_30Jan2024_broken_ttbarCR_selection_logic/THselection_HT750_Data_Run2.root','READ')
a_run2 = ROOT.TFile.Open('root://cmseosmgm01.fnal.gov:1094//store/user/ammitra/topHBoostedAllHad/selection/THselection_HT750_Data_Run2.root','READ')

print('Comparing previous vs new selection yields')
before = 'selection_backup_30Jan2024_broken_ttbarCR_selection_logic/'
after  = 'selection/'
xrdfsls= 'xrdfs root://cmseos.fnal.gov ls'
base = '/store/user/ammitra/topHBoostedAllHad/'

n_before = subprocess.check_output('{} -u {}{} | grep Data | grep -v Muon | grep -v Run2 | grep -v With | grep -v Data_ | wc -l'.format(xrdfsls,base,before),shell=True).strip()
n_after = subprocess.check_output('{} -u {}{} | grep Data | grep -v Muon | grep -v Run2 | grep -v With | grep -v Data_ | wc -l'.format(xrdfsls,base,after),shell=True).strip()

#assert(n_before==n_after)
print('There were {} files before fixing trig eff, and {} files after'.format(n_before,n_after))

b_files = subprocess.check_output('{} -u {}{} | grep Data | grep -v Muon | grep -v Run2 | grep -v With | grep -v Data_'.format(xrdfsls,base,before),shell=True)
a_files = subprocess.check_output('{} -u {}{} | grep Data | grep -v Muon | grep -v Run2 | grep -v With | grep -v Data_'.format(xrdfsls,base,after),shell=True)

b_files = b_files.split('\n')
a_files = a_files.split('\n')

b = [i.strip() for i in b_files if i != '']
a = [i.strip() for i in a_files if i != '']

b_eos = {}
a_eos = {}

hname = 'MthvMh_particleNet_SR_pass__nominal'

for i in range(len(b)):
    before_file = b[i]
    after_file = a[i]

    before_name = '_'.join(before_file.split('/')[-1].split('.')[0].split('_')[2:])
    after_name  = '_'.join(after_file.split('/')[-1].split('.')[0].split('_')[2:])

    b_f = ROOT.TFile.Open(before_file)
    a_f = ROOT.TFile.Open(after_file)

    for region in ['fail','loose','pass']:
	for SRorCR in ['SR','CR']:
	    b_yield = b_f.Get(hname.replace('SR_pass',SRorCR+'_'+region)).Integral()
	    a_yield = a_f.Get(hname.replace('SR_pass',SRorCR+'_'+region)).Integral()
	    if before_name in b_eos:
		b_eos[before_name].update({SRorCR+'_'+region:b_yield})
		a_eos[after_name].update({SRorCR+'_'+region:a_yield})
	    else:
		b_eos[before_name] = {SRorCR+'_'+region:b_yield}
		a_eos[after_name]  = {SRorCR+'_'+region:a_yield}

    for region in ['fail','pass']:
	ttCR_yield_a = a_f.Get(hname.replace('SR_pass','ttbarCR_{}'.format(region))).Integral()
	ttCR_yield_b = b_f.Get(hname.replace('SR_pass','ttbarCR_{}'.format(region))).Integral()
	b_eos[before_name].update({'ttbarCR_%s'%region:ttCR_yield_b})
        a_eos[after_name].update({'ttbarCR_%s'%region:ttCR_yield_a})

    b_f.Close()
    a_f.Close()

#print(b_eos)

for dataset in b_eos.keys():
    print('dataset {} -------------------------------'.format(dataset))
    for SRorCR in ['SR','CR','ttbarCR']:
	for region in ['fail','loose','pass']:
	    if (SRorCR == 'ttbarCR') and (region == 'loose'): continue
	    name = '{}_{}'.format(SRorCR,region)
	    print('{} -------------'.format(name))
	    print('\tbefore: {}'.format(b_eos[dataset][name]))
	    print('\tafter : {}'.format(a_eos[dataset][name]))
	    if b_eos[dataset][name] != a_eos[dataset][name]:
		if 'ttbar' in name: continue
		print('\nERROR - MISMATCH\n')


print('Checking hadd-ed Run2 data files')

by_run2 = b_run2.Get(hname).Integral()
ay_run2 = a_run2.Get(hname).Integral()

print('Run2 SR_pass yield before: {}'.format(by_run2))
print('Run2 SR_pass yield after:  {}'.format(ay_run2))

base_str = ''
for dataset in b_eos.keys():
    base_str += '+{}'.format(a_eos[dataset]['SR_pass'])
print(base_str)

by_run2_ttcr = b_run2.Get(hname.replace('SR_pass','ttbarCR_{}'.format('fail'))).Integral()
ay_run2_ttcr = a_run2.Get(hname.replace('SR_pass','ttbarCR_{}'.format('fail'))).Integral()

print('Run2 ttbarCR_fail yield before: {}'.format(by_run2_ttcr))
print('Run2 ttbarCR_fail yield after: {}'.format(ay_run2_ttcr))

by_run2_ttcr = b_run2.Get(hname.replace('SR_pass','ttbarCR_{}'.format('pass'))).Integral()
ay_run2_ttcr = a_run2.Get(hname.replace('SR_pass','ttbarCR_{}'.format('pass'))).Integral()

print('Run2 ttbarCR_pass yield before: {}'.format(by_run2_ttcr))
print('Run2 ttbarCR_pass yield after: {}'.format(ay_run2_ttcr))

'''
# check that the ttCR yields are the same in the non orthogonal
by_run2_ttcr = b_run2.Get(hname.replace('SR_pass','ttbarCR_{}'.format('fail'))).Integral()
ay_run2_ttcr = a_run2.Get(hname.replace('SR_pass','ttbarCR_{}_notorthog'.format('fail'))).Integral()

print('Run2 ttbarCR_fail yield before: {}'.format(by_run2_ttcr))
print('Run2 ttbarCR_fail (nonorthog) yield after: {}'.format(ay_run2_ttcr))

# check that the ttCR yields are the same in the non orthogonal
by_run2_ttcr = b_run2.Get(hname.replace('SR_pass','ttbarCR_{}'.format('pass'))).Integral()
ay_run2_ttcr = a_run2.Get(hname.replace('SR_pass','ttbarCR_{}_notorthog'.format('pass'))).Integral() 
print('Run2 ttbarCR_pass yield before: {}'.format(by_run2_ttcr))
print('Run2 ttbarCR_pass (nonorthog) yield after: {}'.format(ay_run2_ttcr))
'''
