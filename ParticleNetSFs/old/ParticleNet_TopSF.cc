#include<ROOT/RVec.hxx>
#include <TRandom.h>
#include <string>
#include <iostream>
#include <stdio.h>
#include <vector>

/*
 * Class for applying ParticleNet top-tagging scale factors on a jet-by jet basis.
 * Method used:
 * https://twiki.cern.ch/twiki/bin/viewauth/CMS/BTagSFMethods#2a_Jet_by_jet_updating_of_the_b
 *
 * The original tagger categories will have been created using CreateTopTaggingCategories(),
 * in THmodules.cc. This will result in each event having a vector of ints representing the 
 * original top categories of all jets in the event (0:fail, 1:pass). 
 *
 * In both the CR and SR, we begin by picking the top jet from the two candidate jets, this will
 * naturally select the other jet as the phi. 
 */

using namespace ROOT::VecOps;

class PNetTopSFHandler {
    private:
	float _wp;		// 0.94
	float _effIdx0;		// MC efficiency calculated using TIMBER. Only needed if SF>1
	float _effIdx1;
	std::string _year;	// 2016APV, 2016, 2017, 2018
	int _var;		// 0: nominal, 1: up, 2: down, passed to constructor
	std::pair<int,int> _idxs;	// indices of the two candidate jets in Dijet {0,1}
	TRandom _rand;		// used for random number generation
	int _newTags_idx0[2] = {0,0};	// number of jets in each new category [fail][pass]
	int _origTags_idx0[2] = {0,0};	// original number of jets in each category
        int _newTags_idx1[2] = {0,0};   // number of jets in each new category [fail][pass]
        int _origTags_idx1[2] = {0,0};  // original number of jets in each category	

	// SF[_var][pt] (_var: 0=nom, 1=up, 2=down)
	// variations are described above, pt cats are [300, 400), [400, 480), [480, 600), [600, 1200) across all years
	// Scale factors located at:
	// https://indico.cern.ch/event/1152827/contributions/4840404/attachments/2428856/4162159/ParticleNet_SFs_ULNanoV9_JMAR_25April2022_PK.pdf
        // HP (tight WP)
    	float SF2016APV_T[3][4] = {{1.10,1.06,1.04,1.00},{1.18,1.13,1.11,1.21},{1.03,1.00,0.98,0.91}};
    	float SF2016_T[3][4]    = {{0.97,0.91,0.99,1.00},{1.07,0.96,1.05,1.09},{0.89,0.86,0.94,0.92}};
    	float SF2017_T[3][4]    = {{1.12,0.96,1.00,0.93},{1.24,1.01,1.05,0.98},{1.02,0.92,0.95,0.87}};
    	float SF2018_T[3][4]    = {{1.03,0.95,0.91,0.95},{1.12,1.00,0.95,1.02},{0.95,0.90,0.88,0.90}};
    	// MP (loose WP)
    	float SF2016APV_L[3][4] = {{1.23,1.07,1.04,1.06},{1.39,1.17,1.18,1.24},{1.09,1.02,0.99,0.96}};
    	float SF2016_L[3][4]    = {{1.08,0.99,1.03,1.29},{1.19,1.05,1.10,1.54},{0.98,1.04,0.98,1.03}};
    	float SF2017_L[3][4]    = {{1.11,1.01,1.05,1.00},{1.23,1.05,1.14,1.06},{1.03,0.97,1.01,0.96}};
    	float SF2018_L[3][4]    = {{1.19,0.98,0.96,0.97},{1.31,1.02,1.00,1.02},{1.07,0.94,0.93,0.92}};

    public:
	PNetTopSFHandler(float wp, std::pair<float,float> eff, std::string year, std::pair<int,int> idxs, int var);
	~PNetTopSFHandler();
	float getSF(int jetCat, float pt);	// determine SF based on jet's pT, original category, and internal variables (_year, _var)
	RVec<int> updateTag(RVec<int> jetCat, RVec<float> pt);	// determine the jet's new tagger category using the original categories from THmodules.cc
	void printVals();	// print the number of original and new jets
	int getNewCat(float SF, int oldCat, float eff, double rand);	// based on the jet's SF, original category, and random number, determine n
};

PNetTopSFHandler::PNetTopSFHandler(float wp, std::pair<float,float> eff, std::string year, std::pair<int,int> idxs, int var) {
    _wp = wp;
    _effIdx0 = eff.first;
    _effIdx1 = eff.second;
    _year = year;
    _idxs = idxs;
    _var = var;
};

PNetTopSFHandler::~PNetTopSFHandler() {
    printVals();
};

/*
 * Takes in the original tagger category as jetCat
 */
float PNetTopSFHandler::getSF(int jetCat, float pt) {
    float SF;
    int ptCat;
    // get the pT category
    if ((pt >= 300) && (pt < 400))	 { ptCat = 0; }
    else if ((pt >= 400) && (pt < 480))	 { ptCat = 1; }
    else if ((pt >= 480) && (pt < 600))	 { ptCat = 2; }
    else if ((pt >= 600) && (pt < 1200)) { ptCat = 3; }
    else { return 1.0; }
    // get SF
    switch (jetCat) {
	case 0:	// jet is originally in fail 
	    if (_year=="2016APV") { SF = SF2016APV_L[_var][ptCat]; }
	    else if (_year=="2016") { SF = SF2016_L[_var][ptCat]; }
	    else if (_year=="2017") { SF = SF2017_L[_var][ptCat]; }
	    else { SF = SF2018_L[_var][ptCat]; }
	case 1: // jet originally in pass
            if (_year=="2016APV") { SF = SF2016APV_T[_var][ptCat]; }
            else if (_year=="2016") { SF = SF2016_T[_var][ptCat]; }
            else if (_year=="2017") { SF = SF2017_T[_var][ptCat]; }
            else { SF = SF2018_T[_var][ptCat]; }
    }
    return SF;
};

/*
 * Takes in the original top tag category vectors
 */
RVec<int> PNetTopSFHandler::updateTag(RVec<int> jetCat, RVec<float> pt) {
    // initialize output vector
    RVec<int> out(2);
    // now get the info from the two jets 
    int jetCatIdx0 = jetCat[_idxs.first];	// original top tag category jet 0
    int jetCatIdx1 = jetCat[_idxs.second];	// original top tag category jet 1
    float ptIdx0 = pt[_idxs.first];		// pt jet 0
    float ptIdx1 = pt[_idxs.second];		// pt jet 1
    // update number of original tags
    _origTags_idx0[jetCatIdx0]++;
    _origTags_idx1[jetCatIdx1]++;
    // now store relevant variables
    float effIdx0 = _effIdx0;
    float effIdx1 = _effIdx1;
    float SFIdx0 = getSF(jetCatIdx0, ptIdx0);
    float SFIdx1 = getSF(jetCatIdx1, ptIdx1);
    // generate a random number for each jet
    double rnIdx0 = _rand.Rndm();
    double rnIdx1 = _rand.Rndm();
    int newCatIdx0 = jetCatIdx0;	// to be updated
    int newCatIdx1 = jetCatIdx1;
    // determine new tagger categories
    newCatIdx0 = getNewCat(SFIdx0, jetCatIdx0, effIdx0, rnIdx0);
    newCatIdx1 = getNewCat(SFIdx1, jetCatIdx1, effIdx1, rnIdx1);
    // update number of new tags
    _newTags_idx0[newCatIdx0]++;
    _newTags_idx1[newCatIdx1]++;
    // assign output
    out[0] = newCatIdx0;
    out[1] = newCatIdx1;
    return out;
};

int PNetTopSFHandler::getNewCat(float SF, int oldCat, float eff, double rand) {
    int newCat;
    if (SF < 1) {
        // downgrade fraction (1-SF) of tagged -> untagged
        if ((oldCat == 1) && (rand < 1.-SF)) { newCat=0; };
    }
    else {
        // upgrade fraction of untagged -> tagged
        if (oldCat == 0) {
            float num = 1.-SF;
            float den = 1.-(1./eff);
            float f = num/den;
            if (rand < f) {
                newCat = 1;
            }
        }
    }
    return newCat;
};

void PNetTopSFHandler::printVals() {
    // prints the number of original and new tagger values
    printf("Number of original top jets (idx0)\n\tFail: %d\n\tPass: %Ad\n\tTotal: %d\n\t", _origTags_idx0[0],_origTags_idx0[1], _origTags_idx0[0]+_origTags_idx0[1]);
    printf("Number of new top jets (idx0)\n\tFail: %d\n\tPass: %Ad\n\tTotal: %d\n\t", _newTags_idx0[0],_newTags_idx0[1],_newTags_idx0[0]+_newTags_idx0[1]);
    printf("Number of original top jets (idx1)\n\tFail: %d\n\tPass: %Ad\n\tTotal: %d\n\t", _origTags_idx1[0],_origTags_idx1[1], _origTags_idx1[0]+_origTags_idx1[1]);
    printf("Number of new top jets (idx1)\n\tFail: %d\n\tPass: %Ad\n\tTotal: %d\n\t", _newTags_idx1[0],_newTags_idx1[1],_newTags_idx1[0]+_newTags_idx1[1]);
};
