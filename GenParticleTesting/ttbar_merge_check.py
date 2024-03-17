#####################################################################
# ttbar_merge_check.py - Lucas Corcodilos 5/4/19                    #
# -----------------------------------------------                   #
# Script to make a generator particle tree from ttbar all-hadronic  #
# decays in NanoAOD format where we attempt to identify the         #
# the daughter Ws and bs and determine if the qs from the W and the #
# b quark are all merged in the reconstructed top jet.              #
# -----------------------------------------------                   #
# Prerequisites                                                     #
# -----------------------------------------------                   #
# * `pip install graphviz` -> python interface to graphiz           #
# * Download and install actual graphviz from here                  # 
#   https://graphviz.gitlab.io/_pages/Download/Download_source.html #
# * Will not work on CMSSW because of these dependencies            #
#####################################################################

import ROOT
from ROOT import *
import math, sys, os
import pprint 
pp = pprint.PrettyPrinter(indent=4)
import GenParticleChecker
from GenParticleChecker import *
import Bstar_Functions_local
from Bstar_Functions_local import *

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection,Object,Event
from PhysicsTools.NanoAODTools.postprocessing.framework.treeReaderArrayTools import InputTree
from PhysicsTools.NanoAODTools.postprocessing.tools import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.JetSysColl import JetSysColl, JetSysObj
from PhysicsTools.NanoAODTools.postprocessing.framework.preskimming import preSkim

def BtagVal(fatjet,subJetsColl):
    if (fatjet.subJetIdx1 < 0) or (fatjet.subJetIdx1 >= len(subJetsColl)):
        if (fatjet.subJetIdx2 < 0) or (fatjet.subJetIdx2 >= len(subJetsColl)):  # if both negative, throw away event
            pass
        else:   # if idx2 not negative or bad index, use that
            btagval = subJetsColl[fatjet.subJetIdx2].btagDeepB

    else:
        if (fatjet.subJetIdx2 < 0) or (fatjet.subJetIdx2 >= len(subJetsColl)): # if idx1 not negative, use that
            btagval = subJetsColl[fatjet.subJetIdx1].btagDeepB
        # if both not negative, use largest
        else:
            btagval = max(subJetsColl[fatjet.subJetIdx1].btagDeepB, subJetsColl[fatjet.subJetIdx2].btagDeepB)

    return btagval

#####################
#####################
## Begin main code ##
#####################
#####################
if os.environ.get('CMSSW_BASE') == None:
    file = TFile.Open('~/CMS/temp/ttbar_bstar18.root')
else:
    file = TFile.Open('root://cmseos.fnal.gov//store/user/lcorcodi/bstar_nano/rootfiles/ttbar_bstar18.root')

Cuts = LoadCuts('ttbar','18')
tau32cut = 'tau32medium'

################################
# Grab event tree from nanoAOD #
################################
inTree = file.Get("Events")
elist,jsonFiter = preSkim(inTree,None,'')   # Needs to be done like this because
inTree = InputTree(inTree,elist)            # TTree does not have entries attribute otherwise
treeEntries = inTree.entries                # Now inTree is a NanoAOD ttree

count = 0

##############
# Begin Loop #
##############
nevents = treeEntries
for entry in range(0,nevents):
    count   =   count + 1
    sys.stdout.write("%i / %i ... \r" % (count,nevents))
    sys.stdout.flush()

    # Grab the event
    event = Event(inTree, entry)

    # Have to grab Collections for each collection of interest
    # -- collections are for types of objects where there could be multiple values
    #    for a single event
    genParticlesColl = Collection(event, 'GenPart')
    ak8JetsColl = Collection(event, 'FatJet')
    subJetsColl = Collection(event, 'SubJet')

    particle_tree = GenParticleTree()

    # Now try to top tag the two leading ak8 jets (no mass requirement)
    leadJet = ak8JetsColl[0]
    subleadJet = ak8JetsColl[1]
    
    if leadJet.pt > 500 and leadJet.eta < 2.4 and subleadJet.pt > 500 and subleadJet < 2.4:
        leadVect, subleadVect = TLorentzVector(), TLorentzVector()
        leadVect.SetPtEtaPhiM(leadJet.pt,leadJet.eta,leadJet.phi,leadJet.msoftdrop)
        subleadVect.SetPtEtaPhiM(subleadJet.pt,subleadJet.eta,subleadJet.phi,subleadJet.msoftdrop)

        if leadVect.DeltaPhi(subleadVect) < math.pi:
            lead_tau32 = leadJet.tau3/leadJet.tau2 if leadJet.tau2 > 0 else 100
            sublead_tau32 = subleadJet.tau3/subleadJet.tau2 if subleadJet.tau2 > 0 else 100

            tau32_bool = (Cuts[tau32cut][0] < lead_tau32 < Cuts[tau32cut][1]) and (Cuts[tau32cut][0] < sublead_tau32 < Cuts[tau32cut][1])
            sjbtag_bool = (Cuts['deepbtag'][0] < BtagVal(leadJet, subJetsColl) < Cuts['deepbtag'][1]) and (Cuts['deepbtag'][0] < BtagVal(subleadJet, subJetsColl) < Cuts['deepbtag'][1])

            if tau32_bool and sjbtag_bool:
                # Build the gen particle tree with relevant particles
                for i,p in enumerate(genParticlesColl):
                    # Internal class info
                    this_gen_part = GenParticleObj(i,p)
                    this_gen_part.SetStatusFlags()
                    this_gen_part.SetPDGName(abs(this_gen_part.pdgId))
                    
                    if abs(this_gen_part.pdgId) == 6:# and this_gen_part.status == 62: # 22 means intermediate part of hardest subprocess, only other to appear is 62 (outgoing subprocess particle with primordial kT included)
                        particle_tree.AddParticle(this_gen_part)

                    elif abs(this_gen_part.pdgId) == 24:# and this_gen_part.status == 22: # 22 means intermediate part of hardest subprocess, only other to appear is 52 (outgoing copy of recoiler, with changed momentum)
                        particle_tree.AddParticle(this_gen_part)

                    elif abs(this_gen_part.pdgId) == 5 and this_gen_part.status == 23:
                        particle_tree.AddParticle(this_gen_part)

                    elif abs(this_gen_part.pdgId) >= 1 and abs(this_gen_part.pdgId) <= 4 and this_gen_part.status == 23:
                        particle_tree.AddParticle(this_gen_part)

                # for top in [p for p in particle_tree.GetParticles() if abs(p.pdgId) == 6 and p.status == 22]:

                #     cursor = top
                #     while cursor:
                #         cursor_children = particle_tree.GetChildren(particle)
                #         if len(cursor_children) == 1: 
                #             cursor = cursor_children[0]
                #         else:
                #             for child in cursor_children:



                #     top_children = particle_tree.GetChildren(particle)

                #     for child in children:
                #         if abs(child.pdgId) == 5:


                particle_tree.FindChain('t>W>b')
                particle_tree.PrintTree(entry,options=['status','statusFlags:fromHardProcess'])
                raw_input('')
