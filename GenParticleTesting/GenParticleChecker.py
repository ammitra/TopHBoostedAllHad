#####################################################################
# GenParticleChecker.py - Lucas Corcodilos 5/3/19                   #
# -----------------------------------------------                   #
# Class that takes in relevant gen particles, identifies            #
# relationships, and draws the tree for each event.                 #
# -----------------------------------------------                   #
# Prerequisites                                                     #
# -----------------------------------------------                   #
# * `pip install graphviz` -> python interface to graphiz           #
# * Download and install actual graphviz from here                  # 
#   https://graphviz.gitlab.io/_pages/Download/Download_source.html #
# * Will not work on CMSSW because of these dependencies            #
#####################################################################

import ROOT
# from ROOT import TLorentzVector

class GenParticleTree:
    def __init__ (self):
        self.nodes = []
        # self.staged_nodes = []
        self.heads = []

    def AddParticle(self, mygenpart):
        self.staged_node = mygenpart
        # First check if current heads don't have new parents and remove them from heads if they do
        heads_to_delete = []
        for i, head in enumerate(self.heads):
            if head.motherIdx == self.staged_node.idx:
                heads_to_delete.append(i)

        for ih in sorted(heads_to_delete, reverse=True): # need to delete indices in reverse order so as not to shift indices after a deletion
            del self.heads[ih]

        # Next identify staged node has no parent (heads)
        # If no parent, no other info we can get from this particle
        if self.staged_node.motherIdx not in [gpo.idx for gpo in self.nodes]:
            self.heads.append(self.staged_node)
            self.nodes.append(self.staged_node)

        # If parent, we can find parent and add staged node as the child to the parent
        else:
            for inode, node in enumerate(self.nodes):
                if self.staged_node.motherIdx == node.idx:
                    # print 'Print found edge '+ '%s, %s, %s' % (self.staged_node.name, self.staged_node.status, self.staged_node.motherIdx) + ' - '+ '%s, %s, %s' % (node.name, node.status, node.motherIdx)
                    self.staged_node.AddParent(inode)
                    node.AddChild(len(self.nodes))
                    self.nodes.append(self.staged_node)

    def GetParticles(self):
        return self.nodes

    def GetChildren(self,particle):
        children = []
        for i in particle.childIndex:
            children.append(self.nodes[i])
        return children

    def GetParent(self,particle):
        if len(particle.parentIndex) == 0:
            return False
        else:
            return self.nodes[particle.parentIndex[0]]

    def GetParents(self,particle):
        parents = []
        for i in particle.parentIndex:
            parents.append(self.nodes[i])
        return parents

    def MatchParticleToString(self,part,string):
        #print('Matching %s/%s to %s' %(part.name,part.pdgId,string))
        if ':' in string:
            pdgIds = range(int(string.split(':')[0]),int(string.split(':')[1])+1)
        #elif ',' in string:
            #pdgIds = [int(s) for s in string.split(',')]
	elif ',' in string:
	    pdgIds = [s for s in string.split(',')]
        else: pdgIds = False

        if pdgIds == False:
	    #print('DEBUG: ',part.name)
            if part.name == string : return True#or abs(part.pdgId) == int(string): return True
            else: return False
        else:
            #if abs(part.pdgId) in pdgIds: return True
	    if part.name in pdgIds: return True
            else: return False

    def RunChain(self,node,chain):
        # print 'Chain: %s' % chain
        # print 'Current node: %s'%node.pdgId
        nodechain = [node]
        parent = self.GetParent(node)
        if len(chain) == 0: 
            pass
        elif parent == False:
            #print('Parent is false')
            nodechain.append(False)
        elif self.MatchParticleToString(parent,chain[0]):
            #print('Match found for %s, %s. Evaluating %s, %s' %(parent.pdgId,chain[0],[parent.pdgId],chain[1:]))
            nodechain.extend(self.RunChain(parent,chain[1:]))
        elif parent.pdgId == node.pdgId:
            #print('Parent is copy. Evaluating %s, %s' %([parent.pdgId],chain))
            nodechain.extend(self.RunChain(parent,chain))
        else:
            #print('No candidate parent. Parent.pdgId is %s. Looking for %s' % (parent.pdgId,chain))
            nodechain.append(False)

        return nodechain

    def FindChain(self,chainstring):
        reveresedchain = chainstring.split('>')
        reveresedchain.reverse()
	#print('REVERSED CHAIN:',reveresedchain)
        returnresult = []

        for n in self.nodes:
	    #print('Checking node: %s'%n.name) 
            if self.MatchParticleToString(n,reveresedchain[0]):
		#print('Running chain for %s, %s'%(n.name,reveresedchain[1:]))
                chainresult = self.RunChain(n,reveresedchain[1:])
                if False not in chainresult: returnresult.append(chainresult)

        if len(returnresult) == 0: return False
        else: return returnresult

    def PrintTree(self,ievent,options=[],name='test',jet=None,dRs=None,nmerged=None):  # final option is list of other attributes of GenParticleObj to draw
        from graphviz import Digraph
        dot = Digraph(comment='Particle tree for event '+str(ievent),format='svg')

        for n in self.nodes:
            this_node_name = 'idx_'+str(n.idx)
            this_node_label = n.name

            # Build larger label if requested
            for o in options:
                if 'statusFlags' in o:
                    flag = o.split(':')[1]
                    this_node_label += '\n%s = %s'%(flag,n.statusFlags[flag])
                elif 'vect' in o:
                    kin = o.split(':')[1]
                    this_node_label += '\n%s=%s'%(kin,getattr(n.vect,kin)())
                else:
                    this_node_label += '\n%s=%s'%(o,getattr(n,o))

            if jet != None:
                this_node_label += '\n%s=%.2f'%('\Delta R with jet',n.DeltaR(jet))

	    node_color = False
	    if n.childIndex == []: 	# final state particle found
	    	if (dRs != None):	# we have information about dR with parent top
		    for i in dRs:
			if n.idx == i[0]:
		    	    dR = i[-1]
		    	    this_node_label += '\ndR = %.2f'%(dR)
			    if dR <= 0.8:
				node_color = '#00FF00'
			    else:
				node_color = '#FF0000'
			else:
			    continue

	    # set everything up
	    if not node_color:
            	dot.node(name=this_node_name, label=this_node_label)
	    else:
		# have to use str() here, weird bug
		# https://github.com/viewflow/django-fsm/issues/169#issuecomment-380461984
		dot.node(name=this_node_name, label=this_node_label, style=str('filled'), fillcolor=str(node_color))

            for ichild in n.childIndex:
                dot.edge(this_node_name, 'idx_'+str(self.nodes[ichild].idx))

	if nmerged:
	    dot.attr(label=str('Top merged: %s\nW merged: %s\nUnmerged: %s'%(nmerged[0],nmerged[1],nmerged[2])))

        dot.render('particle_trees/'+name+'_'+str(ievent))


class GenParticleObj:
    def __init__ (self, index, genpart):
        self.idx = index
        self.genpart = genpart
        self.status = genpart.status
        self.statusFlagsInt = genpart.statusFlags
        self.pdgId = genpart.pdgId
        self.name = ''
        self.vect = ROOT.Math.PtEtaPhiMVector(genpart.pt,genpart.eta,genpart.phi,genpart.mass)
        self.pt = self.vect.Pt()
        self.eta = self.vect.Eta()
        self.phi = self.vect.Phi()
        self.mass = self.vect.M()
        self.motherIdx = genpart.genPartIdxMother

        self.statusFlags = {}

        # For GenParticleTree interface
        self.parentIndex = []
        self.childIndex = []

        self.Constants()
        self.SetStatusFlags()


    def Constants(self):
        self.GenParticleStatusFlags = {
            'isPrompt': 0,
            # 'isDecayedLeptonHadron': 1,
            # 'isTauDecayProduct': 2,
            # 'isPromptTauDecayProduct': 3,
            # 'isDirectTauDecayProduct': 4,
            # 'isDirectPromptTauDecayProduct': 5,
            'isDirectHadronDecayProduct': 6,
            'isHardProcess': 7,
            'fromHardProcess': 8,
            # 'isHardProcessTauDecayProduct': 9,
            # 'isDirectHardProcessTauDecayProduct': 10,
            'fromHardProcessBeforeFSR': 11,
            'isFirstCopy': 12,
            'isLastCopy': 13,
            'isLastCopyBeforeFSR': 14
        }
        self.PDGIds = {
            1:'d', 2:'u', 3:'s', 4:'c', 5:'b', 6:'t',
            11:'e', 12:'nu_e', 13:'mu', 14:'nu_mu', 15:'tau', 16:'nu_tau',
            21:'g', 22:'photon', 23:'Z', 24:'W', 25:'h'
        }

    # Compare to jet and do basic tests of proximity
    def CompareToJet(self,jetvect):
        sameHemisphere = True if self.vect.DeltaPhi(jetvect) < math.pi else False
        deltaR = self.DeltaR(jetvect) < 0.8
        deltaM = (abs(jetvect.M() - self.vect.M())/self.vect.M() < 0.05)

        return {'sameHemisphere':sameHemisphere,'deltaR':deltaR,'deltaM':deltaM}

    def DeltaR(self,vect):
        return ROOT.Math.VectorUtil.DeltaR(self.vect,vect)

    # Set individual flags
    def SetStatusFlags(self):
        for key in self.GenParticleStatusFlags.keys():
            self.statusFlags[key] = bitChecker(self.GenParticleStatusFlags[key], self.statusFlagsInt)

    def GetStatusFlag(self, flagName):
        return self.statusFlags[flagName]

    # Set name of particle (should come from PDG ID code)
    def SetPDGName(self,code):
        if code in self.PDGIds.keys():
            self.name = self.PDGIds[abs(code)]
        else:
            self.name = str(code)

    # Store an index for GenParticleTree parent
    def AddParent(self,index):
        self.parentIndex.append(index)

    def AddChild(self,index):
        self.childIndex.append(index)

# Evaluates bit stored in an integer
def bitChecker(bit, number):
    result = number & (1 << bit)
    if result > 0:
        return True
    else:
        return False
