from TIMBER.Analyzer import Correction, CutGroup, ModuleWorker, analyzer
from TIMBER.Tools.Common import CompileCpp
from TIMBER.CollectionOrganizer import *
from THClass import THClass
import ROOT

CompileCpp('CheckTopMerging.cc')
CompileCpp('THmodules.cc')

# open a ttbar file
#ttbar_file = 'dijet_nano/ttbar-allhad_17_snapshot.txt'
ttbar_file = 'ttbar-allhad_16_snapshot_first_100_events.txt'
selection = THClass(ttbar_file,16,1,1)  # only run on one file
era=16

# now run the basic corrections on it
selection.OpenForSelection('None')
trigEff = Correction("TriggerEff%s"%era,'EffLoader_2DfittedHist.cc',['out_Eff_20%s.root'%era,'Eff_20%s'%era],corrtype='weight')
selection.ApplyTrigs(trigEff)
kinOnly = selection.a.MakeWeightCols(extraNominal='' if selection.a.isData else 'genWeight*%s'%selection.GetXsecScale())

# get the existing collections
#collectionOrg = selection.a._collectionOrg
# define our structure in memory
#struct_str = StructDef_new(collectionOrg,'GenPart')
#print("Defining struct:")
#print(struct_str)
#print('')
#CompileCpp(struct_str)

# now we want to make a vector of these structs 
name = 'GenPart'
selection.a.Define('GenPartStruct_vec','make_GenPart_vec(n{0},{0}_status,{0}_phi,{0}_statusFlags,{0}_pt,{0}_pdgId,{0}_eta,{0}_mass,{0}_genPartIdxMother)'.format(name))
#display = selection.a.DataFrame.Display("")
#display.Print()

top_tagger = 'particleNet_TvsQCD'
higgs_tagger = 'particleNetMD_HbbvsQCD'

# identify the higgs and top candidate jets
tt_checkpoint = selection.ApplyTopPick(tagger=top_tagger,invert=False,CRv2=higgs_tagger)

# now run our genmatching script
selection.a.Define('NMerged_1','NMerged(Top_vect,GenPartStruct_vec)')

norm = 'genWeight*%s'%selection.GetXsecScale()
selection.a.Define('norm',norm)

hist1 = selection.a.DataFrame.Histo1D(('nmerged1','N_{subjets} top cand - before selection',4,0,4),'NMerged_1','norm')

signal = False
# Make the SR
passfailSR = selection.ApplyHiggsTag('SR', tagger=higgs_tagger, signal=signal)
# Make the ttbarCR
selection.a.SetActiveNode(tt_checkpoint)
passFailttCR = selection.Create_ttbarCR(higgsTagger=higgs_tagger, topTagger='deepTagMD_TvsQCD', signal=signal, loose=False)

hists = [hist1]
# loop over, find NMerged for both top and higgs(phi) 
region_selection_dict = {"SR":passfailSR,"ttbarCR":passFailttCR}
for rkey, rpair in region_selection_dict.items():
    for pfkey, node in rpair.items():
        print('Analyzing %s %s....'%(rkey,pfkey))
	region = '%s_%s'%(rkey,pfkey)
        selection.a.SetActiveNode(node)
	selection.a.Define('NMerged_%s_Top'%(region),'NMerged(Top_vect,GenPartStruct_vec)')
	selection.a.Define('NMerged_%s_Phi'%(region),'NMerged(Higgs_vect,GenPartStruct_vec)')
	selection.a.Define('NSplit_%s_Top'%(region),'TopSplitting(Top_vect,GenPartStruct_vec)')
	selection.a.Define('NSplit_%s_Phi'%(region),'TopSplitting(Higgs_vect,GenPartStruct_vec)')
	histo_top = selection.a.DataFrame.Histo1D(('nmerged_top_%s'%(region),'N_{subjets} top cand - %s'%(region),4,0,4),'NMerged_%s_Top'%(region))
	histo_phi = selection.a.DataFrame.Histo1D(('nmerged_phi_%s'%(region),'N_{subjets} phi cand - %s'%(region),4,0,4),'NMerged_%s_Phi'%(region))
	split_top = selection.a.DataFrame.Histo1D(('split_top_%s'%(region),'Split category top cand - %s'%(region),7,-1,6),'NSplit_%s_Top'%(region))
	split_phi = selection.a.DataFrame.Histo1D(('split_phi_%s'%(region),'Split category phi cand - %s'%(region),7,-1,6),'NSplit_%s_Phi'%(region))

	hists.append(histo_top)
	hists.append(histo_phi)
	hists.append(split_top)
	hists.append(split_phi)

fout = ROOT.TFile.Open('TEST_NMERGED.root','RECREATE')
fout.cd()
c = ROOT.TCanvas('c','c')
c.cd()
c.Clear()
c.Print("TEST_NMERGED.pdf[")
for hist in hists:
    c.Clear()
    hist.Draw()
    hist.Write()
    c.Print("TEST_NMERGED.pdf")

c.Print('TEST_NMERGED.pdf]')
fout.Close()


'''
# Now make the SR
tt_checkpoint = selection.ApplyTopPick(tagger=top_tagger,invert=False,CRv2=higgs_tagger)
selection.a.Define
passfailSR = selection.ApplyHiggsTag('SR', tagger=higgs_tagger, signal=signal)
# now make the ttbarCR
selection.a.SetActiveNode(tt_checkpoint)
passFailttCR = selection.Create_ttbarCR(higgsTagger=higgs_tagger, topTagger='deepTagMD_TvsQCD', signal=signal, loose=False)

region_selection_dict = {"SR":passfailSR,"ttbarCR":passFailttCR}
for rkey, rpair in region_selection_dict.items():
    for pfkey, node in rpair.items():
	print('Analyzing %s %s....'%(rkey,pfkey))
	selection.a.SetActiveNode(node)
	selection.a.Define('%s_%s_Top_GenPartStruct'%(rkey,pfkey),

GenPartStruct(Int_t status,Float_t phi,Int_t statusFlags,Float_t pt,Int_t pdgId,Float_t eta,Float_t mass,Int_t genPartIdxMother)
'''





'''
struct_str = StructDef_new(collectionOrg,'GenPart')
print('The struct is....')
print(struct_str)

print('Compiling struct for C++/Cling...')
CompileCpp(struct_str)

collectionName = 'GenPart'
varList = collectionOrg.GetCollectionAttributes(collectionName)
struct_obj = StructObj(collectionName,varList)
print('script to make the vector of structs')
print(struct_obj)
print('Instantiating an object of the struct...')
#CompileCpp(struct_obj)
a.Define('test',struct_str)
'''



