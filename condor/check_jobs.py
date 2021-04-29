import glob, os, subprocess, time
from argparse import ArgumentParser
from TIMBER.Tools.Common import DictToMarkdownTable

def GetJobNumber(logname):
    return logname[:-4].split('_')[-1]

# Check there are logs for each job 
def CheckLogsExist(logsList):
    nJobs = 0
    for l in allLogs:
        jobNumber = GetJobNumber(l)
        if int(jobNumber) >= nJobs: 
            nJobs = int(jobNumber)+1

    if len(allLogs) != nJobs: # ERROR: These don't match!
        if len(allLogs) < nJobs:
            logNameTemplate = allLogs[0]
            jobNumber = GetJobNumber(logNameTemplate)
            missing = [] # look for what is missing
            for i in range(0,nJobs):
                logToFind = logNameTemplate.replace(jobNumber,str(i))
                if os.path.exists(logToFind):
                    continue
                else:
                    missing.append(logToFind)

            raise ValueError('The number of logs (%s) is less than the max job number found (%s). Missing logs are '%(len(allLogs), nJobs, missing)) 
        else:
            raise ValueError ('The number of logs (%s) is greater than the max job number found (%s).'%(len(allLogs), nJobs))

def ParseCondorQ(stdout,tasknumber):
    taskDict = {}
    for l in stdout.split('\n'):
        if 'Schedd' in l: # Get schedd
            for piece in [i.strip() for i in l.split(' ')]:
                if piece.startswith('lpcschedd'):
                    currentSchedd = piece
                    break
                
        if l.startswith(tasknumber):
            info = [i.strip() for i in l.split(' ') if i != '']
            jobNumber = info[0].split('.')[-1]
            taskDict[jobNumber] = {
                'runtime': info[4],
                'status': info[5],
                'args': ' '.join(info[9:]),
                'schedd': currentSchedd
            }
            if info[5] == 'H':
                taskDict[jobNumber]['holdreason'] = subprocess.check_output('condor_q %s %s.%s -name %s -af HoldReason'%(os.getenv('USER'), args.tasknumber, jobNumber, currentSchedd), shell=True)

    return taskDict

def FindRuntimeLine(lines): # NOTE NOT GENERIC
    runtime = ''
    for i in range(1,101):
        runtimeLine = lines[-1*i]
        if 'sec' in runtimeLine:
            runtime = int( float(runtimeLine.split(' ')[0].strip()) )
            break
    return runtime

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-t', type=str, dest='tasknumber',
                        action='store', required=True,
                        help='Task number to analyze.')
    args = parser.parse_args()

    allLogs = glob.glob('logs/output_%s_*log'%args.tasknumber)
    stdoutArgLine = 'Running ./condor_exec.exe'
    CheckLogsExist(allLogs)

    jobsToReRun = []
    jobsRunning = ParseCondorQ(subprocess.check_output('condor_q %s %s'%(os.getenv('USER'), args.tasknumber), shell=True), args.tasknumber)
    jobsFinished = {}
    # Loop over logs to get status of each job not still running
    for f in allLogs:
        # Check if stdout exists (job not running)
        if os.path.exists(f.replace('.log','.stdout')):
            logLines = open(f,'r').readlines()
            stdoutLines = open(f.replace('.log','.stdout'),'r').readlines()
            stderrLines = open(f.replace('.log','.stderr'),'r').readlines()

            for lstdout in stdoutLines:
                if stdoutArgLine in lstdout:
                    jobargs = lstdout[lstdout.find(stdoutArgLine)+len(stdoutArgLine):]
                    break

            # Check for errors and report back error and job arguments
            hasError = False
            for lstderr in stderrLines:
                if 'error' in lstderr.lower():
                    hasError = True
                    if FindRuntimeLine(stdoutLines) != '':
                        hasError = False
                    if hasError:
                        print ('Found error: %s'%lstderr)
                        print (f.replace('.log','.stderr'))
                        print ('\t%s'%jobargs)
                        print ('Found error: %s'%lstderr)
                        print (f.replace('.log','.stderr'))
                        print ('\t%s'%jobargs)
                        jobsToReRun.append(jobargs)
                    break
            # If no error, get the time to finish
            if not hasError:
                jobsFinished[GetJobNumber(f)] = {
                    'runtime': time.strftime('%H:%M:%S', time.gmtime(FindRuntimeLine(stdoutLines))),
                    'args': jobargs.strip()
                }

    # Now build the report
    print (
'''
SUMMARY
========================================
Finished: {0}, Running: {1}, Failed: {2}
'''.format(len(jobsFinished.keys()),len(jobsRunning.keys()),len(jobsToReRun))
    )

    report = open('logs/report_%s.md'%args.tasknumber,'w')
    report.write('# JOBS SUCCESSFUL\n')
    report.write('| Job Number | Args | Runtime |\n')
    report.write('|------------|------|---------|\n')
    for jobNumber in jobsFinished.keys():
        job = jobsFinished[jobNumber]
        report.write('|'+'|'.join([jobNumber, job['args'], job['runtime']])+'|\n')
    
    report.write('\n')
    report.write('# JOBS RUNNING\n')
    report.write(DictToMarkdownTable(jobsRunning, roworder=sorted(jobsRunning.keys()), columnorder=['args','status','runtime']))

    report.write('\n')
    report.write('# JOBS FAILED\n')
    for a in jobsToReRun:
        report.write(a+'\n')
    report.close()

    rerunList = open('logs/jobsToReRun_%s.txt'%(args.tasknumber),'w')
    rerunList.writelines(jobsToReRun)
    rerunList.close()