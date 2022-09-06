#include <ROOT/RVec.hxx>
#include <iostream>
#include <string>
#include <algorithm>
#include <vector>

/*
 * @class PNetSFHandler
 * @brief Class designed to implement the ParticleNet SFs derived for the T' -> t\phi analysis
 * SFs found at: https://coli.web.cern.ch/coli/.cms/btv/boohft-calib/20220623_bb_TprimeB_useExpr_2016APV/
 *
 * WPs: {HP: [0.98, 1.0], MP: [0.8, 0.98], LP: [0.0, 0.8]}
 * pt: [400, 600), [600, 800), [800, +inf)
 * Years: 2016APV, 2016, 2017, 2018
 */

using namespace ROOT::VecOps;

class PNetSFHandler {
    private:
	std::vector< std::pair<int, std::string> > _variations = {{0, "PNetWeight"}, {1,"PNetWeight_Up"}, {-1,"PNetWeight_Down"}};
	int _variation;		// keeps track of which variation we're performing
	std::string _year;	// string because we have years 2016APV, 2016, 2017, 2018
	float GetScaleFactor(float pt, float score);	// gets the appropriate scale factor based on jet pt, score, and internal variable _variation
    public:
	PNetSFHandler(std::string year); 
	~PNetSFHandler(){};
	// calls GetScaleFactor using the vectors of jet pt and tagger score:
	// Dijet_pt, Dijet_particleNet_HbbvsQCD
	ROOT::VecOps::RVec<float> eval(RVec<float> Jet_pt, RVec<float> tagScore);	// MUST be returned as {nominal, up, down}
};

PNetSFHandler::PNetSFHandler(std::string year) {
    _year = year;
};

// perform horrible boolean logic to get the appropriate SF for event weighting. Maybe there is a better way to do this (mapping)?
// first check score
//   - then check pt 
//     - then check variation
//       - then check year
PNetSFHandler::GetScaleFactor(float pt, float score) {
    float out = 1.0;	// default, no change to event weight

    // regardless of year, if the event doesn't meet pT or tag score we drop it
    if ((score < 0.8) || (pt < 400.0)) {
	return out;
    }

    // MP working point: [0.8, 0.98]
    if ((score > 0.8) && (score < 0.98)) {
	// now check pt
	if ((pt >= 400) && (pt < 600)) {
	    switch (_variation) {
		case 0:	    // nominal
		    if (_year == "2016APV") {
			out = 1.163;
		    }
		    else if (_year == "2016") {
			out = 1.012;
		    }
		    else if (_year == "2017") {
			out = 0.946;
		    }
		    else {
			out = 1.020;
		    }
		case 1:    // up
                    if (_year == "2016APV") {
                        out = 1.163 + 0.274;
                    }
                    else if (_year == "2016") {
                        out = 1.012 + 0.168;
                    }
                    else if (_year == "2017") {
                        out = 0.946 + 0.129;
                    }
                    else {
                        out = 1.020 + 0.126;
                    }
		case -1:    // down 
                    if (_year == "2016APV") {
                        out = 1.163 - 0.214;
                    }
                    else if (_year == "2016") {
                        out = 1.012 - 0.113;
                    }
                    else if (_year == "2017") {
                        out = 0.946 - 0.116;
                    }
                    else {
                        out = 1.020 - 0.126;
                    }
	    }
	}
	else if ((pt >= 600) && (pt < 800)) {
	    switch (_variation) {
		case 0:    // nominal
                    if (_year == "2016APV") {
                        out = 1.206;
                    }
                    else if (_year == "2016") {
                        out = 1.247;
                    }
                    else if (_year == "2017") {
                        out = 1.027;
                    }
                    else {
                        out = 1.013;
                    }
		case 1:    // up
                    if (_year == "2016APV") {
                        out = 1.206 + 0.323;
                    }
                    else if (_year == "2016") {
                        out = 1.247 + 0.262;
                    }
                    else if (_year == "2017") {
                        out = 1.027 + 0.131;
                    }
                    else {
                        out = 1.013 + 0.097;
                    }
		case -1:    // down
                    if (_year == "2016APV") {
                        out = 1.206 - 0.214;
                    }
                    else if (_year == "2016") {
                        out = 1.247 - 0.113;
                    }
                    else if (_year == "2017") {
                        out = 1.027 - 0.116;
                    }
                    else {
                        out = 1.013 - 0.126;
                    }
	    }	
	}
	else {    // 800-infty
	    switch (_variation) {
                case 0:    // nominal
                    if (_year == "2016APV") {
                        out = 1.491;
                    }
                    else if (_year == "2016") {
                        out = 1.188;
                    }
                    else if (_year == "2017") {
                        out = 0.900;
                    }
                    else {
                        out = 1.082;
                    }
		case 1:    // up
                    if (_year == "2016APV") {
                        out = 1.491 + 0.592;
                    }
                    else if (_year == "2016") {
                        out = 1.188 + 0.236;
                    }
                    else if (_year == "2017") {
                        out = 0.900 + 0.126;
                    }
                    else {
                        out = 1.082 + 0.158;
                    }
		case -1:    // down
                    if (_year == "2016APV") {
                        out = 1.491 - 0.582;
                    }
                    else if (_year == "2016") {
                        out = 1.188 - 0.228;
                    }
                    else if (_year == "2017") {
                        out = 0.900 - 0.148;
                    }
                    else {
                        out = 1.082 - 0.121;
                    }
	    }
	}
    }
    
    // now tight working point, [0.98, 1.0]
    if ((score > 0.98) && (score < 1.0)) {
	// now check pt
	if ((pt >= 400) && (pt < 600)) {
	    switch (_variation) {
		case 0:    // nominal
                    if (_year == "2016APV") {
                        out = 1.102;
                    }
                    else if (_year == "2016") {
                        out = 1.032;
                    }
                    else if (_year == "2017") {
                        out = 0.973;
                    }
                    else {
                        out = 0.904;
                    }
		case 1:    // up
                    if (_year == "2016APV") {
                        out = 1.102 + 0.219;
                    }
                    else if (_year == "2016") {
                        out = 1.032 + 0.102;
                    }
                    else if (_year == "2017") {
                        out = 0.973 + 0.053;
                    }
                    else {
                        out = 0.904 + 0.062;
                    }
		case -1:    // down
                    if (_year == "2016APV") {
                        out = 1.102 - 0.184;
                    }
                    else if (_year == "2016") {
                        out = 1.032 - 0.100;
                    }
                    else if (_year == "2017") {
                        out = 0.973 - 0.069;
                    }
                    else {
                        out = 0.904 - 0.080;
                    }
	    }
	}
	else if ((pt >= 600) && (pt < 800)) {
	    switch (_variation) {
		case 0:    // nominal
                    if (_year == "2016APV") {
                        out = 1.103;
                    }
                    else if (_year == "2016") {
                        out = 1.173;
                    }
                    else if (_year == "2017") {
                        out = 1.006;
                    }
                    else {
                        out = 0.921;
                    }
		case 1:    // up
                    if (_year == "2016APV") {
                        out = 1.103 + 0.252;
                    }
                    else if (_year == "2016") {
                        out = 1.173 + 0.209;
                    }
                    else if (_year == "2017") {
                        out = 1.006 + 0.058;
                    }
                    else {
                        out = 0.921 + 0.048;
                    }
		case -1:    // down
                    if (_year == "2016APV") {
                        out = 1.103 - 0.232;
                    }
                    else if (_year == "2016") {
                        out = 1.173 - 0.203;
                    }
                    else if (_year == "2017") {
                        out = 1.006 - 0.075;
                    }
                    else {
                        out = 0.921 - 0.080;
                    }
	    }
	}
	else {    // pt [800, inf)
	    switch (_variation) {
		case 0:    // nominal
                    if (_year == "2016APV") {
                        out = 1.434;
                    }
                    else if (_year == "2016") {
                        out = 1.145;
                    }
                    else if (_year == "2017") {
                        out = 1.059;
                    }
                    else {
                        out = 1.087;
                    }
		case 1:    // up
                    if (_year == "2016APV") {
                        out = 1.434 + 0.480;
                    }
                    else if (_year == "2016") {
                        out = 1.145 + 0.187;
                    }
                    else if (_year == "2017") {
                        out = 1.059 + 0.073;
                    }
                    else {
                        out = 1.087 + 0.078;
                    }
		case -1:    // down
                    if (_year == "2016APV") {
                        out = 1.434 - 0.479;
                    }
                    else if (_year == "2016") {
                        out = 1.145 - 0.191;
                    }
                    else if (_year == "2017") {
                        out = 1.059 - 0.077;
                    }
                    else {
                        out = 1.087 - 0.112;
                    }
	    }
	}
    }
    return out;
};


PNetSFHandler::eval(RVec<float> Jet_pt, RVec<float> tagScore) {
    std::string branchname;
    RVec<float> out(3)
    for (size_t i=0; i<_variations.size(); i++) {
	_variation = _variations[i].first;	// 0: nominal, 1: up, -1: down
	branchname = _variations[i].second;
	// now that we have a given variation, loop over all signal jets and apply SF
	for (size_t ijet=0; ijet<Jet_pt.size(); ijet++) {
	    // do we multiply the score by this SF value? or just create a weight column??
	    // for now, just create a weight column based on the jet's pT and score 

	}
    }
};
