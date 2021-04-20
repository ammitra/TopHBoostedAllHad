# Analysis Strategy

Dijet search for boosted X -> top+Higgs. The benchmark, X, is a VLQ T' produced
in association with a bottom quark. The interaction with an associated top quark
is currently ignored since the simulation samples are inconsistent with the UL
versions available for all other MC. The associated quark will have 
much lower transverse momentum than the T' decay products and so the affect on
the analysis is expected to be small (ie. quark will be along beamline).

# Processing Pipeline
## 0. The generic THClass
The THClass holds inside of it all of the basic, generic logic to perform the selection.
Any additions, modifications, splittings, or saving of the selection should be added here.
Subsequent steps should always interface with this so that if something is changed, it's propagated
to the full pipeline.
## 1. Grab latest raw NanoAOD file locations
The list of file locations in `raw_nano/` can be easily populated with
```
python raw_nano/get_all_lpc.py
```
If one wishes to add to the sets considered, simply modify the dictionary
in `raw_nano/get_all_lpc.py` with the name of the set and the DAS path.
## 2. Perform snapshot on `raw_nano/` files
The command to perform one snapshot using `THsnapshot.py` is 
```python
THsnapshot.py -s <setname> -y <16,17,18> -j <ijob> -n <njobs>
```
where `<ijob>` and `<njobs>` determine the job number and the number of jobs to split into and default
to 1 and 1, respectively.

### Condor
#### Preparing an archived environment
The `condor/tar_env.sh` script will create a tarball of the current environment and store
it on EOS. 

**NOTE 1:** You may need to modify this if you are not on LPC or wish to store the tarball somewhere else.
**NOTE 2:** If you are a TIMBER developer, you need to rerun this script everytime you change TIMBER to
ensure the condor node has your latest changes.
#### Arguments file
To generate the arguments to submit to condor, use `python condor/snapshot_args.py` which will
dynamically read the contents of `raw_nano/` to create a list of arguments for condor in `condor/snapshot_args.txt`.
This script will also split sets into N/2 jobs where N is the total number of raw NanoAOD files. This splitting is
quite aggressive to keep job runtimes under the 4 hour mark and can be changed as needed.

#### Bash script to run on condor node
The script that will run on the node is `condor/run_snapshot.sh`. You may need to modify it to suite your needs
but even without modifications, one needs to ensure that the `topHBoostedAllHad` exists on their EOS space.
To create it on LPC, run
```
eosmkdir /store/user/<username>/topHBoostedAllHad
```
#### Submission
To submit to condor, create a symbolic link to TIMBER's CondorHelper.py,
```
ln -s $TIMBERPATH/TIMBER/Utilities/Condor/CondorHelper.py
```

Then run 
```
python CondorHelper.py -r condor/run_snapshot.sh -a condor/snapshot_args.txt -i "THClass.py THsnapshot.py helpers.py"`
```
where `-i` argument is just an example of how to ship local scripts that you may have changed and want to include (without
having to run `condor/tar_env.sh`). You can add or remove the files here as you see fit.

To check on jobs, run `condor_q <username>`.

**NOTE:** This step assumes you have performed the previous steps of creating an environment tarball and creating a list of
jobs to submit in the condor task.

## 3. Collect condor snapshot outputs
Job outputs will automatically be moved to your EOS in the `condor/run_snapshot.sh` script that runs
per-job on the condor nodes. The information for these can be collected with
```
python dijet_nano/get_all.py
```
This script will dynamically search the EOS folder where the outputs are stored and populate the lists
based on these. **NOTE** this means that only jobs that have finished successfully will be grabbed. If
a job is still running or failed, it will not be included.

### Checking job success
The most fool-proof method is to read the stdout/stderr of each job but this is of course very time consuming.
A helper script (which is not promised to be fool-proof!) that can automate the most basic checks is 
provided in `python condor/check_jobs.py -t <tasknumber>`. The task number is reported at several points
but can be found in two ways post-submission depending on the stage of your jobs.
- If your jobs are still running, the return of `condor_q <username>` will show lines like
```
-- Schedd: lpcschedd1.fnal.gov : <131.225.188.55:9618?... @ 04/20/21 14:56:24
 ID          OWNER            SUBMITTED     RUN_TIME ST PRI SIZE  CMD
12513846.51  lcorcodi        4/19 23:03   0+15:49:47 R  0   607.0 run_snapshot.sh -s ttbar -y 17
12513846.65  lcorcodi        4/19 23:03   0+15:49:21 R  0   625.0 run_snapshot.sh -s ttbar -y 16

Total for query: 2 jobs; 0 completed, 0 removed, 0 idle, 2 running, 0 held, 0 suspended 
Total for all users: 4650 jobs; 0 completed, 114 removed, 111 idle, 1866 running, 2559 held, 0 suspended
```
In this example, `12513846` is the task number.

- If your jobs are complete, the outputs in `logs/` will have the task number in their names. For a file
named `logs/output_12513846_51.stdout`, the task number is again `12513846`.

The `condor/check_jobs.py` will check for python errors in the `stderr` as well as the final
time-to-finish number reported at the end of successful job in `stdout`. It will collect information
on jobs finished, failed, and still running (if they exist) and prepare a report (`logs/report_<tasknumber>.txt`) which includes
job runtimes (for those that have finished), a new set of arguments for resubmission of failed jobs (`logs/jobsToReRun_<tasknumber>.txt`),
and jobs still running (and if they are in the Hold state, what the reason is).

* - A "task" is the basket that "jobs" fall into - one `CondorHelper.py` call creates one "task" with several "jobs".

## 4. Final selections and studies
Once you are sure the snapshots are finished and available and their locations have been accessed,
the basic selection can be performed with `python THselection.py -s <setname> -y <year>`. This script
will take in the corresponding txt file in `dijet_nano/*.txt` and perform the basic signal region and "fail" region
selections and makes 2D histograms for 2D Alphabet. However, any other selection or study 
can follow a similar format to perform more complicated manipulation of the snapshots.

# Data and simulation
2016
| Setname | DAS location |
|---------|--------------|
| DataB1 | /JetHT/Run2016B-ver1_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD |
| DataB2 | /JetHT/Run2016B-ver2_HIPM_UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD |
| QCDHT2000 | /QCD_HT2000toInf_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| QCDHT700 | /QCD_HT700to1000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| DataH | /JetHT/Run2016H-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD |
| TprimeB 800 GeV | /TprimeBToTH_M-800_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| TprimeB 900 GeV | /TprimeBToTH_M-900_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| TprimeB 1000 GeV | /TprimeBToTH_M-1000_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| TprimeB 1100 GeV | /TprimeBToTH_M-1100_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| TprimeB 1200 GeV | /TprimeBToTH_M-1200_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| TprimeB 1300 GeV | /TprimeBToTH_M-1300_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| TprimeB 1400 GeV | /TprimeBToTH_M-1400_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| TprimeB 1500 GeV | /TprimeBToTH_M-1500_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| TprimeB 1600 GeV | /TprimeBToTH_M-1600_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| TprimeB 1700 GeV | /TprimeBToTH_M-1700_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| TprimeB 1800 GeV | /TprimeBToTH_M-1800_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| DataE | /JetHT/Run2016E-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD |
| DataD | /JetHT/Run2016D-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD |
| DataG | /JetHT/Run2016G-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD |
| DataF | /JetHT/Run2016F-UL2016_MiniAODv1_NanoAODv2-v2/NANOAOD |
| DataC | /JetHT/Run2016C-UL2016_MiniAODv1_NanoAODv2-v1/NANOAOD |
| QCDHT1500 | /QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| ttbar | /TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| ttbar-semilep | /TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |
| QCDHT1000 | /QCD_HT1000to1500_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL16NanoAODv2-106X_mcRun2_asymptotic_v15-v1/NANOAODSIM |

2017
| Setname | DAS location |
|---------|--------------|
| QCDHT1000 | /QCD_HT1000to1500_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| QCDHT2000 | /QCD_HT2000toInf_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| QCDHT700 | /QCD_HT700to1000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| TprimeB 800 GeV | /TprimeBToTH_M-800_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| TprimeB 900 GeV | /TprimeBToTH_M-900_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| TprimeB 1000 GeV | /TprimeBToTH_M-1000_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| TprimeB 1100 GeV | /TprimeBToTH_M-1100_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| TprimeB 1200 GeV | /TprimeBToTH_M-1200_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| TprimeB 1300 GeV | /TprimeBToTH_M-1300_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| TprimeB 1400 GeV | /TprimeBToTH_M-1400_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| TprimeB 1500 GeV | /TprimeBToTH_M-1500_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| TprimeB 1600 GeV | /TprimeBToTH_M-1600_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| TprimeB 1700 GeV | /TprimeBToTH_M-1700_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| TprimeB 1800 GeV | /TprimeBToTH_M-1800_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| DataE | /JetHT/Run2017E-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD |
| DataD | /JetHT/Run2017D-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD |
| DataF | /JetHT/Run2017F-UL2017_MiniAODv1_NanoAODv2-v2/NANOAOD |
| DataC | /JetHT/Run2017C-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD |
| DataB | /JetHT/Run2017B-UL2017_MiniAODv1_NanoAODv2-v1/NANOAOD |
| QCDHT1500 | /QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| ttbar | /TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |
| ttbar-semilep | /TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL17NanoAODv2-106X_mc2017_realistic_v8-v1/NANOAODSIM |

2018
| Setname | DAS location |
|---------|--------------|
| QCDHT1000 | /QCD_HT1000to1500_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| QCDHT2000 | /QCD_HT2000toInf_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| QCDHT700 | /QCD_HT700to1000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| TprimeB 800 GeV | /TprimeBToTH_M-800_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| TprimeB 900 GeV | /TprimeBToTH_M-900_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| TprimeB 1000 GeV | /TprimeBToTH_M-1000_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| TprimeB 1100 GeV | /TprimeBToTH_M-1100_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| TprimeB 1200 GeV | /TprimeBToTH_M-1200_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| TprimeB 1300 GeV | /TprimeBToTH_M-1300_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| TprimeB 1400 GeV | /TprimeBToTH_M-1400_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| TprimeB 1500 GeV | /TprimeBToTH_M-1500_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| TprimeB 1600 GeV | /TprimeBToTH_M-1600_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| TprimeB 1700 GeV | /TprimeBToTH_M-1700_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| TprimeB 1800 GeV | /TprimeBToTH_M-1800_LH_TuneCP5_PSweights_13TeV-madgraph_pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| DataD | /JetHT/Run2018D-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD |
| DataA | /JetHT/Run2018A-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD |
| DataC | /JetHT/Run2018C-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD |
| DataB | /JetHT/Run2018B-UL2018_MiniAODv1_NanoAODv2-v1/NANOAOD |
| QCDHT1500 | /QCD_HT1500to2000_TuneCP5_PSWeights_13TeV-madgraphMLM-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| ttbar | /TTToHadronic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |
| ttbar-semilep | /TTToSemiLeptonic_TuneCP5_13TeV-powheg-pythia8/RunIISummer19UL18NanoAODv2-106X_upgrade2018_realistic_v15_L1v1-v1/NANOAODSIM |

# Selections

## Signal Region
| Variable      | Selection                 |
|---------------|---------------------------|
| p_T           | Both jets, > 350 GeV      |
| abs(\eta)     | Both jets, < 2.4          |
| \Delta \phi   | > M_PI/2                  |
| Top tag       | DeepAK8 MD > 0.632 + 105 < mSD < 210 (5% mistag) |
| Higgs tag     | **DeepAK8 MD > 0.9**|

## QCD-enriched region (fail)
| Variable      | Selection                 |
|---------------|---------------------------|
| p_T           | Both jets, > 350 GeV      |
| abs(\eta)     | Both jets, < 2.4          |
| \Delta \phi   | > M_PI/2                  |
| Top tag       | DeepAK8 MD < 0.632 + 105 < mSD < 210 (5% mistag) |
| Higgs tag     | **DeepAK8 MD < 0.9** |

# Open questions
- Do we use a tight and loose Higgs tag as in B2G-20-004?
If so, what regions are available for the "fail" of 2D Alphabet?
- Need the Higgs tagging SFs from B2G-20-004
- Are the tagging WPs optimal?
- Do we have any other kinematic cuts to make (delta eta or delta rapidity)?
- Can we switch to the ParticleNet taggers?
    - **Answer: Yes**
- Can we try using pT cut of 400 GeV or higher to ensure the top merges?
    - **Answer: Yes**
- Do we want to make the top the alphabet side?
    - **Answer: No. There are lots of ttbar events so establishing how much top doesn't tell you how much tH there are. On the other hand, the SM background for H+X is tiny.  So, finding H inside the preselection that includes top and QCD on the other side makes it much more likely that this is what we are looking for. You additionally avoid your signal jet mass being on top of the top jet mass ridge and instead it lives in the flat area of 100-140 GeV.**

