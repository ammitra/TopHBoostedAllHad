'''
script to check which snapshot jobs are missing on the EOS
'''
import subprocess

eosls = 'eos root://cmseos.fnal.gov ls'
eosdir = '/store/user/ammitra/topHBoostedAllHad/snapshot/'

def get_raw_processes():
    '''gets all raw NANOOAD processes'''
    procs_raw = subprocess.check_output('ls raw_nano/ | grep .txt',shell=True,text=True).split('\n')
    procs = [i.split('.txt')[0] for i in procs_raw if 'txt' in i]
    return procs

def get_eos_snapshots():
    '''gets all existing EOS snapshots in a list'''
    snaps_raw = subprocess.check_output('%s %s'%(eosls,eosdir),shell=True,text=True).split('\n')
    snaps = [i for i in snaps_raw if 'snapshot' in i]
    return snaps

def get_process(snapshot_list, procname):
    '''from the snapshot list, isolate only the given process'''
    proc = procname.split('_')[0]
    year = procname.split('_')[-1]
    to_check = '_%s_%s_'%(proc,year) # format will be THsnapshot_proc_year_XofY.root
    procs = [i for i in snapshot_list if to_check in i]
    return procs

def get_total(proc_list):
    '''from the list of a given process, check how many jobs were submitted'''
    if len(proc_list) == 0:
        return 0
    else:
        base = int(proc_list[0].split('.root')[0].split('of')[-1]) # compare all against this
        for i in proc_list:
            assert(int(i.split('.root')[0].split('of')[-1]) == base)
        return base

def find_missing(proc_list):
    '''from the list of a given process, check which jobs are missing'''
    total = int(proc_list[0].split('.root')[0].split('of')[-1])
    done = [int(i.split('.root')[0].split('of')[0].split('_')[-1]) for i in proc_list]
    done.sort()
    full = [i for i in range(1,total+1)] # get the list of all files that would be complete
    missing = list(set(done) ^ set(full))
    return [str(i) for i in missing]

def make_rerun_string(missing, procname, total):
    '''for the given process and missing jobs, make the string for Condor rerun args'''
    out_args = []
    name = procname.split('_')[0]
    year = procname.split('_')[-1]
    for ijob in missing:
        out_str = ' -s %s -y %s -j %s -n %s'%(name, year, ijob, total)
        out_args.append(out_str)
    return out_args

def make_rerun_args(jobs_to_rerun):
    '''from a list of all arguments for jobs to rerun, write to file'''
    with open('snapshot_jobs_to_rerun.txt','w') as f:
        for line in jobs_to_rerun:
            f.write('%s\n'%line)

def get_null_jobs(procname, arg_list):
    '''if no jobs found on EOS, get the jobs from the snapshot arg.txt file and append'''
    name = procname.split('_')[0]
    year = procname.split('_')[-1]
    return [i for i in arg_list if '-s {} -y {} '.format(name,year) in i]

if __name__ == "__main__":
    snapshot_args_txt = open('condor/snapshot_args.txt','r').readlines()
    snapshot_args_txt = [i.strip() for i in snapshot_args_txt]
    procs_raw = get_raw_processes()	# all processes in raw_nano/
    snaps_eos = get_eos_snapshots()	# all processes on EOS snapshot dir
    jobs_to_rerun = []
    # check each process
    for proc_raw in procs_raw:
        proc_eos = get_process(snaps_eos, proc_raw)  # list of only the current process
        proc_tot = get_total(proc_eos)
        procs_found = len(proc_eos)
        if procs_found == 0:
            print('-------------------------------- %s --------------------------------'%proc_raw)
            print('WARNING: No snapshots found on EOS for process %s\n'%proc_raw)
            out_args = get_null_jobs(proc_raw, snapshot_args_txt)
            for arg in out_args:
                jobs_to_rerun.append(arg)
        if procs_found == proc_tot:
            continue
        else:
            print('-------------------------------- %s --------------------------------'%proc_raw)
            print('There were %s jobs submitted for process %s'%(proc_tot, proc_raw))
            print('\t%s/%s snapshots found on EOS'%(procs_found,proc_tot))
            missing = find_missing(proc_eos)
            print('\tMissing job #%s\n'%','.join(missing))
            out_args = make_rerun_string(missing, proc_raw, proc_tot)
            for arg in out_args:
                jobs_to_rerun.append(arg)
    make_rerun_args(jobs_to_rerun)

