#include <string>
#include <vector>
#include <ROOT/RVec.hxx>
#include <utility>	// pair

using namespace ROOT::VecOps;
/**
 * @brief C++ class to handle ParticleNet W-tagging scale factor weighting, based on
 * method 1c) https://twiki.cern.ch/twiki/bin/viewauth/CMS/BTagSFMethods#1c_Event_reweighting_using_scale
 */
class PNetTopTag_weight {
  private:
    // Scale Factor values taken from: 
    // https://indico.cern.ch/event/1152827/contributions/4840404/attachments/2428856/4162159/ParticleNet_SFs_ULNanoV9_JMAR_25April2022_PK.pdf
    // SF[_var][pt] (_var: 0=nom, 1=up, 2=down)
    // variations are described above, pt cats are [300, 400), [400, 480), [480, 600), [600, 1200) across all years
    // HP (tight)
    float SF2016APV_T[3][4] = {{1.10,1.06,1.04,1.00},{1.18,1.13,1.11,1.21},{1.03,1.00,0.98,0.91}};
    float SF2016_T[3][4]    = {{0.97,0.91,0.99,1.00},{1.07,0.96,1.05,1.09},{0.89,0.86,0.94,0.92}};
    float SF2017_T[3][4]    = {{1.12,0.96,1.00,0.93},{1.24,1.01,1.05,0.98},{1.02,0.92,0.95,0.87}};
    float SF2018_T[3][4]    = {{1.03,0.95,0.91,0.95},{1.12,1.00,0.95,1.02},{0.95,0.90,0.88,0.90}};
    // MP (loose)
    float SF2016APV_L[3][4] = {{1.23,1.07,1.04,1.06},{1.39,1.17,1.18,1.24},{1.09,1.02,0.99,0.96}};
    float SF2016_L[3][4]    = {{1.08,0.99,1.03,1.29},{1.19,1.05,1.10,1.54},{0.98,1.04,0.98,1.03}};
    float SF2017_L[3][4]    = {{1.11,1.01,1.05,1.00},{1.23,1.05,1.14,1.06},{1.03,0.97,1.01,0.96}};
    float SF2018_L[3][4]    = {{1.19,0.98,0.96,0.97},{1.31,1.02,1.00,1.02},{1.07,0.94,0.93,0.92}};
    // store year
    std::string _year;
    // determine jet pT category
    int PTCategory(float jetPt);
    // variation information
    std::vector<std::pair<int, std::string>> _variations = {{0,"PNetTopSFWeight"}, {1,"PNetTopSFWeight_Up"}, {2,"PNetTopSFWeight_Down"}};
    int _var;
    // Function for performing top tagging to determine number of top jets in event
    // First value is the number of top-tagged jets in the event
    // Second value is a pair containing the pT categories of the jet(s) which are top-tagged 
    // In the event only one jet is top tagged, assign the first value of the nested pair to store the pT category information
    std::pair<int,std::pair<int,int>> GetNumberTopTags(RVec<float> pt, RVec<float> topScore, RVec<int> idxs, float scoreCut);
  public:
    // year of signal sample (16, 16APV, 17, 18)
    PNetTopTag_weight(std::string year);
    ~PNetTopTag_weight();
    // main function, returns vector of floats containing {nom, up, down} weights
    RVec<float> eval(RVec<float> pt, RVec<float> topScore, RVec<int> idxs, float scoreCut);
};

// constructor only takes year for determining which SF to use
PNetTopTag_weight::PNetTopTag_weight(std::string year) {
    _year = year;
};

// nothing to do on destruction 
PNetTopTag_weight::~PNetTopTag_weight() {};

// determine an input jet's pT category
int PNetTopTag_weight::PTCategory(float jetPt) {
    if ((jetPt >= 300) && (jetPt < 400)) return 0;
    else if ((jetPt >= 400) && (jetPt < 480)) return 1;
    else if ((jetPt >= 480) && (jetPt < 600)) return 2;
    else if ((jetPt >= 600) && (jetPt < 1200)) return 3;
    // not in our category, return -1 to indicate no weight should be applied
    else return -1;
}

// Using the Top score of the two candidate jets, determines how many top candidates there are in event, as well as pT category of top(s)
// These values then gets passed to the eval() function for determination of the nominal, up, down weights
std::pair<int, std::pair<int,int>> PNetTopTag_weight::GetNumberTopTags(RVec<float> pt, RVec<float> topScore, RVec<int> idxs, float scoreCut) {
    if (idxs.size() > 2) {
	std::cout << "PNetTopTag_weight::GetNumberTopTags -- WARNING: You have input more than two indices. Only two accepted. Assuming first two indices.";
    }
    // store information on number of tops and their pT categories 
    int numTops;
    int ptCat0;
    int ptCat1;
    std::pair<int,int> ptPair;
    std::pair<int,std::pair<int,int>> out;
    // determine which of the jets, if any, are top-tagged
    int idx0 = idxs[0];
    int idx1 = idxs[1];
    bool isTop0, isTop1;
    // begin logic to determine which of the jets is a top
    isTop0 = (topScore[idx0] > scoreCut);
    isTop1 = (topScore[idx1] > scoreCut);
    // determine number of top jets in event
    if (isTop0 && isTop1) {
	// both candidates are tops
	numTops = 2;
	// determine pT categories 
	ptCat0 = PTCategory(pt[idx0]);
	ptCat1 = PTCategory(pt[idx1]);	
	// make the pair and return it
	ptPair = std::make_pair(ptCat0, ptCat1);
	out = std::make_pair(numTops, ptPair);
	return out;
    }
    // the ! convert the values to booleans and negate them, 
    // so that two unequal positive integers (each a true) would evaluate to false.
    else if (!isTop0 != !isTop1) { // logical XOR
	// only one of the two candidates is a top, determine which one and it's pT category
	numTops = 1;
	if (isTop0) {
	    ptCat0 = PTCategory(pt[idx0]);
	    // make the pair and return it
	    ptPair = std::make_pair(ptCat0, -1);
	    out = std::make_pair(numTops, ptPair);
	    return out;
	}
	else {
	    ptCat1 = PTCategory(pt[idx1]);
            // make the pair and return it
            ptPair = std::make_pair(ptCat1, -1);
            out = std::make_pair(numTops, ptPair);
	    return out;
	}
    }
    else {	// neither jet is a top 
	numTops = 0;
	ptPair = std::make_pair(-1, -1);
	out = std::make_pair(numTops, ptPair);
	return out;
    }
};

// Main function, will be called when creating a TIMBER Correction. 
// Takes in the top scores of all jets in the event and passes it to GetNumberTopTags() to get the
// number of top-tagged jets in the event. Then uses that number to calculate event weights 
// and returns a vector of floats with {nom, up, down} weights
RVec<float> PNetTopTag_weight::eval(RVec<float> pt, RVec<float> topScore, RVec<int> idxs, float scoreCut) {
    // initialize weight value
    float weight;
    // initialize output vector
    RVec<float> out(3);
    // get the number of top-tagged jets of our two candidates in this event
    std::pair<int, std::pair<int,int>> results = GetNumberTopTags(pt, topScore, idxs, scoreCut);
    int numJets = results.first;
    // loop over all variations
    for (size_t i=0; i<_variations.size(); i++) {
	_var = _variations[i].first;	// integer representing nom,up,down
	//_branchname = _variations[i].second;	// name of new weight branch
	// determine what SF to apply (SF acts as pseudo-probability)
	switch(numJets) {
	    case 0: {	// neither candidate jet is a top, no weight applied
		weight = 1.;
		break;
	    }
	    case 1: {	// w(0|1) = (1-SF)
		// the pt category of the top-tagged jet will be the first index of the nested pair
		float SF;
		int ptCat = results.second.first;
		if (ptCat < 0) {		// the jet was not in any of the pt categories
		    weight = 1.;	// return no weight
		    break;
		}
		if (_year == "16APV") { SF = SF2016APV_T[_var][ptCat]; }
		else if (_year == "16") { SF = SF2016_T[_var][ptCat]; }
		else if (_year == "17") { SF = SF2017_T[_var][ptCat]; }
		else { SF = SF2018_T[_var][ptCat]; }
		weight = 1. - SF;
	 	break;   
	    }
	    case 2: {	// w(0|2) = (1-SF1)(1-SF2)
		float SF1, SF2;
		int ptCat0 = results.second.first;
		int ptCat1 = results.second.second;
		if (ptCat0 < 0) {
		    SF1 = 0;
		}
		if (ptCat1 < 0) {
		    SF2 = 0;
		}
		// SF1
		if ((_year == "16APV") && !(ptCat0 < 0)) { SF1 = SF2016APV_T[_var][ptCat0]; }
		if ((_year == "16") && !(ptCat0 < 0)) { SF1 = SF2016_T[_var][ptCat0]; }
		if ((_year == "17") && !(ptCat0 < 0)) { SF1 = SF2017_T[_var][ptCat0]; }
		if ((_year == "18") && !(ptCat0 < 0)) { SF1 = SF2018_T[_var][ptCat0]; }
		// SF2
                if ((_year == "16APV") && !(ptCat1 < 0)) { SF2 = SF2016APV_T[_var][ptCat1]; }
                if ((_year == "16") && !(ptCat1 < 0)) { SF2 = SF2016_T[_var][ptCat1]; }
                if ((_year == "17") && !(ptCat1 < 0)) { SF2 = SF2017_T[_var][ptCat1]; }
                if ((_year == "18") && !(ptCat1 < 0)) { SF2 = SF2018_T[_var][ptCat1]; }
		weight = (1.-SF1)*(1.-SF2);
		break;
	    }
	}
    out[i] = weight;
    }
    return out;
};
