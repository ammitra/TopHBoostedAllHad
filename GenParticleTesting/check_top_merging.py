#####################################################################
# check_top_merging.py - Amitav Mitra 3/16/2024                     #
# ----------------------------------------------------------------- #
# Script to make a generator particle tree from ttbar all-hadronic  #
# decays in NanoAOD format where we attempt to identify all of the  #
# daughter Ws and bs. The top quarks will be identified as either:  #
#	1. Top merged: all quarks from W as well as b quark are     #
#	   merged with the jet (DeltaR < 0.8)                       #
#	2. W merged: only quarks from the W are merged with the jet #
#	3. Non-merged: no quarks are merged 			    #
#####################################################################

import ROOT
from ROOT import *
import math, sys, os
import pprint
pp = pprint.PrettyPrinter(indent=4)
import GenParticleChecker
from GenParticleChecker import *

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection,Object,Event
from PhysicsTools.NanoAODTools.postprocessing.framework.treeReaderArrayTools import InputTree
from PhysicsTools.NanoAODTools.postprocessing.tools import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.JetSysColl import JetSysColl, JetSysObj
from PhysicsTools.NanoAODTools.postprocessing.framework.preskimming import preSkim

infile = TFile.Open('ttbar-allhad_16_1of36_first100Events.root')

################################
# Grab event tree from nanoAOD #
################################
inTree = infile.Get("Events")
elist,jsonFiter = preSkim(inTree,None,'')
inTree = InputTree(inTree,elist)
treeEntries = inTree.entries

count = 0

##############
# Begin Loop #
##############
nevents = 50

def get_final_chain(gen_particle_tree, chain_str, verbose=False):
    '''Obtains the final decay chain given a requested decay
    E.g. "T>W>u,d,s,c" will return the decay chains of the final state particles
    from the original top quarks.

    Returns:
	final decay chain(s) as a string
	whether or not the final decay product is merged with the top quark vector
    '''
    if verbose: print('Analyzing decay %s'%chain_str.replace('>',' -> '))
    chains = gen_particle_tree.FindChain(chain_str)
    final_decay_chains = []
    top_children_idxs  = []
    for i, chain in enumerate(chains):
	# output is given from daughter -> mother, so just reverse
	chain.reverse()
	# check if the final particle has any children, if not then we have our final state decay
	for particle in chain:
	    # identify the N distinct top quarks
	    if particle.name == 't':
		if particle.childIndex in top_children_idxs:
		    pass
		else:
		    top_children_idxs.append(particle.childIndex)	    
	    # identify the final state decay chains
	    else:
		if particle.childIndex == []:
		    final_decay_chains.append(chain)
		else:
		    continue
    # now that we have the final state chains, check for merging
    if verbose: print('There were %s top quarks produced'%len(top_children_idxs))
    top_n_chain  = {i:[] for i in range(len(top_children_idxs))}
    top_n_deltaR = {i:[] for i in range(len(top_children_idxs))}
    for chain in final_decay_chains:
	which_top = top_children_idxs.index(chain[0].childIndex) # get the index of the top in the list of N tops
	# make the formatted text decay string
	chain_str = ' -> '.join([particle.name for particle in chain])
	top_n_chain[which_top].append(chain_str)
	# calculate DeltaR between the top and the final particle.
	deltaR = chain[0].DeltaR(chain[-1].vect)
	top_n_deltaR[which_top].append((chain[-1].idx,deltaR))

    # now loop over the N tops 
    for top, decays in top_n_chain.items():
	if verbose: print('Top quark %s:'%(int(top)+1))
	for i, decay in enumerate(decays):
	    if verbose: 
		print('\t'+decay)
		print('\t\tDeltaR(%s,%s) = %s'%(decay[0],decay[-1],top_n_deltaR[top][i]))

    # send back the information
    return final_decay_chains, top_n_chain, top_n_deltaR


for entry in range(0,nevents):
    count   =   count + 1
    #sys.stdout.write("%i / %i ... \r" % (count,nevents))
    #sys.stdout.flush()

    print('------------------- Event %s / %s -------------------'%(count,nevents))

    # Grab the event
    event = Event(inTree, entry)

    # Build collections
    genParticlesColl = Collection(event, 'GenPart')
    # Build generator particle tree
    particle_tree = GenParticleTree()

    # Build the tree with relevant particles
    for i,p in enumerate(genParticlesColl):
        # Internal class info
        this_gen_part = GenParticleObj(i,p)
        this_gen_part.SetStatusFlags()
        this_gen_part.SetPDGName(abs(this_gen_part.pdgId))

	# top quark
        if abs(this_gen_part.pdgId) == 6:
            particle_tree.AddParticle(this_gen_part)

	# W boson
        elif abs(this_gen_part.pdgId) == 24:
            particle_tree.AddParticle(this_gen_part)

	# b quark 
        elif abs(this_gen_part.pdgId) == 5 and this_gen_part.status == 23:
            particle_tree.AddParticle(this_gen_part)

        elif abs(this_gen_part.pdgId) >= 1 and abs(this_gen_part.pdgId) <= 4:# and this_gen_part.status == 23:
            particle_tree.AddParticle(this_gen_part)

    verbose = False

    final_particle_tree = GenParticleTree()

    final_chain_tW, chain_tW, dRs_tW = get_final_chain(particle_tree,'t>W>u,d,s,c', verbose=verbose)
    final_chain_tb, chain_tb, dRs_tb = get_final_chain(particle_tree,'t>b', verbose=verbose) 

    # Track the number of merged tops
    n_topMerged = 0	# bqq
    n_Wmerged   = 0	# qq(+)
    n_unmerged  = 0	# no b,qs

    for top, dRs in dRs_tW.items():
	AreWsMerged = []
 	# First check if W is merged
	for idx, dR in dRs:
	    if dR <= 0.8: 
		AreWsMerged.append(True)
	    else:
		AreWsMerged.append(False)
	# Now check if b associated to this top is merged
	isBmerged = True
	if (len(dRs_tb[top]) == 0):
	    n_unmerged += 1
	    isBmerged = False
	    continue
	else:
	    assert(len(dRs_tb[top]) == 1)
	    for idx, dR in dRs_tb[top]:
		if dR <= 0.8:
		    isBmerged = True
		else:
		    isBmerged = False 

	# determine which of the categories this top falls into
	if (sum(AreWsMerged) >= 2) and (isBmerged):
	    n_topMerged += 1
	elif (sum(AreWsMerged) >= 2) and not (isBmerged):
	    n_Wmerged += 1
	elif (sum(AreWsMerged) < 2):
	    n_unmerged += 1

    if verbose:
	print('---------------------------------------------')
	print('-\t Top merged: %s'%(n_topMerged))
	print('-\t W merged:   %s'%(n_Wmerged))
	print('-\t unmerged:   %s'%(n_unmerged))
	print('---------------------------------------------')

    # pass the dR information of the final state particles so it can be included in diagram
    all_dRs = []
    for top in dRs_tW.keys():
	all_dRs.extend(dRs_tW[top])
	all_dRs.extend(dRs_tb[top])
    nmerged = [n_topMerged,n_Wmerged,n_unmerged]
    if verbose: particle_tree.PrintTree(entry,options=['statusFlags:fromHardProcess'],dRs=all_dRs,nmerged=nmerged)

    raw_input('')
