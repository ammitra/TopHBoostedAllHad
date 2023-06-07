#include "ROOT/RVec.hxx"
#include "TIMBER/Framework/include/common.h"
#include <string>
#include <vector>
#include <random> // because TRandom wouldn't work in this case..

using namespace ROOT::VecOps;

/*****************************************************************
 *  Lepton veto functions 
 *  ---------------------
 *  Loops over all leptons in an event and returns true if 
 *  a lepton in the event meets the criteria for vetoing the 
 *  event. These functions should return a True if the criteria
 *  is met and False if the criteria is not met. The user is 
 *  in charge of correctly interpreting the results of the 
 *  function return, i.e., in an RDataFrame Filter() call.
 *****************************************************************/
bool TightMuVeto(int nMuon, RVec<bool> tightId, RVec<float> muonPt, RVec<float> muonRelIso, RVec<float> muonEta) {
    if (nMuon < 1) {return false;}	// don't veto event, there are no muons
    bool veto = false;
    for (int iMu = 0; iMu < muonPt.size(); iMu++) {
	veto = (tightId[iMu] == 1) && (muonPt[iMu] > 30.) && (muonRelIso[iMu] < 0.15) && (std::abs(muonEta[iMu]) < 2.4); // veto if meets SL selection criteria
	if (veto) {return veto;}
    }
    return veto;
} 

bool TightElVeto(int nElectron, RVec<bool> elIso, RVec<float> elPt, RVec<float> elEta) {
    if (nElectron < 1) {return false;}
    bool veto = false;
    for (int iEl = 0; iEl < elPt.size(); iEl++){
	veto = (elIso[iEl] == 1) && (elPt[iEl] > 35.) && (std::abs(elEta[iEl])<2.5);
	if (veto) {return veto;}
    }
    return veto;
}

bool GoodMuVeto(int nMuon, RVec<float> muonPt, RVec<bool> looseId, RVec<float> dxy, RVec<float> muonEta) {
    if (nMuon < 1) {return false;}
    bool veto = false;
    for (int iMu = 0; iMu < muonPt.size(); iMu++) {
	veto = (muonPt[iMu] > 30.) && (looseId[iMu] == 1) && (std::abs(dxy[iMu]) < 0.02) && (std::abs(muonEta[iMu]) < 2.4);
	if (veto) {return veto;} 
    }
    return veto;
}

bool GoodElVeto(int nElectron, RVec<float> elPt, RVec<bool> elIso, RVec<float> dxy, RVec<float> elEta) {
    if (nElectron < 1) {return false;}
    bool veto =false;
    for (int iEl = 0; iEl < elPt.size(); iEl++) {
	veto = (elPt[iEl] > 35.) && (elIso[iEl] == 1) && (std::abs(dxy[iEl]) < 0.05) && (std::abs(elEta[iEl]) < 2.5);
	if (veto) {return veto;}
    }
    return veto;
}
// -------------------------------------------------------------------------------

double RAND() {
    const double from = 0.0;
    const double to = 1.0;
    std::random_device rand_dev;
    std::mt19937 generator(rand_dev());
    std::uniform_real_distribution<double> distr(from, to);
    return distr(generator);
}

float getSF(int jetCat, float pt, std::string _year, int _var) {
    if ((jetCat!=0) && (jetCat!=1)) {std::cerr<<"ERROR - INITIAL JET CATEGORY MUST BE 0 or 1. Current value is " << jetCat << std::endl;}
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
    // begin logic
    float SF;
    int ptCat;
    // get the pT category
    if ((pt >= 300) && (pt < 400))       { ptCat = 0; }
    else if ((pt >= 400) && (pt < 480))  { ptCat = 1; }
    else if ((pt >= 480) && (pt < 600))  { ptCat = 2; }
    else if ((pt >= 600) && (pt < 1200)) { ptCat = 3; }
    else { return 1.0; }
    // get SF
    switch (jetCat) {
        case 0: { // jet is originally in fail
            if (_year=="2016APV") { SF = SF2016APV_L[_var][ptCat]; }
            else if (_year=="2016") { SF = SF2016_L[_var][ptCat]; }
            else if (_year=="2017") { SF = SF2017_L[_var][ptCat]; }
            else { SF = SF2018_L[_var][ptCat]; }
	    break;
	}
        case 1: { // jet originally in pass
            if (_year=="2016APV") { SF = SF2016APV_T[_var][ptCat]; }
            else if (_year=="2016") { SF = SF2016_T[_var][ptCat]; }
            else if (_year=="2017") { SF = SF2017_T[_var][ptCat]; }
            else { SF = SF2018_T[_var][ptCat]; }
	    break;
	}
    }
    if (SF<0.7) {std::cerr << "SF is " << SF << " for variation " << _var << " and ptCat " << ptCat << std::endl;}
    return SF;
}

int getOriginalTopCat(float TvsQCD, float WP) {
    if (TvsQCD > WP) {return 1;}    // pass
    else {return 0;}                // fail
}

int getNewTopCat(float SF, int oldCat, float eff, double rand, bool invert) {
    int newCat = oldCat;    // to be (possibly) updated
    if (SF < 1) {
        // downgrade fraction (1-SF) of tagged -> untagged
        if ((oldCat == 1) && (rand < 1.-SF)) { 
	    newCat=0; 
	}
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
    //delete random;
    return newCat;
};

RVec<int> PickTopWithSFs(RVec<float> TvsQCD, 
                  RVec<float> HbbvsQCD, 
                  RVec<float> pt, 
		  RVec<float> mass,
                  RVec<int> idxs, 
                  float scoreCut, 
                  float eff0,
                  float eff1,
                  std::string year,
                  int variation,
                  bool invertScore=false) {
    if (idxs.size() > 2) {
        std::cout << "PickTop - WARNING: You have input more than two indices. Only two jet indices accepted, assuming first two indices.\n";
    }

    std::vector<int> out(2);
    float WP = scoreCut;
    int idx0 = idxs[0];
    int idx1 = idxs[1];

    // first, need to determine original tagger categories for each jet 
    int orig_score0 = getOriginalTopCat(TvsQCD[idx0], WP);
    int orig_score1 = getOriginalTopCat(TvsQCD[idx1], WP);
    // now, determine new tagger category
    float SF0 = getSF(orig_score0, pt[idx0], year, variation);
    float SF1 = getSF(orig_score1, pt[idx1], year, variation);
    if ((SF0==0) || (SF1==0)) {std::cerr<<"SF is 0\n";}
    double rand0 = RAND();
    double rand1 = RAND();
    int new_score0 = getNewTopCat(SF0, orig_score0, eff0, rand0, invertScore);
    int new_score1 = getNewTopCat(SF1, orig_score1, eff1, rand1, invertScore);

    // now perform top selection using the new tagger "scores" (aka categories)
    bool isTop0, isTop1;
    if (!invertScore) {
        isTop0 = (new_score0 == 1);
        isTop1 = (new_score1 == 1);
    }
    else {// higgs veto, use raw HbbvsQCD score.
	// NEW 6/7/23 - implement top mass window on 'lead' jet
        isTop0 = (new_score0 == 0) && (HbbvsQCD[idx0] < 0.2) && (mass[idx0]>150) && (mass[idx0]<200);
        isTop1 = (new_score1 == 0) && (HbbvsQCD[idx1] < 0.2);
    }
    // determine which is which 
    if (isTop0 && isTop1) {
	// DEBUG
	//std::cout << "PICKTOP (SIGNAL) - event has 2 top jets\n";
        // if both pass as Top, use the raw TvsQCD score to determine which is "real" top
        if (TvsQCD[idx0] > TvsQCD[idx1]) {
            out[0] = idx0;
            out[1] = idx1;
        }
        else {
            out[0] = idx1;
            out[1] = idx0;
        }
    }
    else if (isTop0) {
	// DEBUG
	//std::cout << "PICKTOP (SIGNAL) - event has 1 top jet\n";
        out[0] = idx0;
        out[1] = idx1;
    }
    else if (isTop1) {
	// DEBUG
	//std::cout << "PICKTOP (SIGNAL) - event has 1 top jet\n";
        out[0] = idx1;
        out[1] = idx0;
    }
    else {
	// DEBUG
	//std::cout << "PICKTOP (SIGNAL) - event has NO top jets\n";
        out[0] = -1;
        out[1] = -1;
    }
    return out;
}

RVec<int> PickDijetsNminus1(RVec<float> phi) {
    // used for Nminus1 testing (only kinematic cut here will be deltaPhi)
    int jet0Idx = -1;
    int jet1Idx = -1;
    for (int ijet=0; ijet<phi.size(); ijet++) {
	if (jet1Idx == -1) {
	    if (jet0Idx == -1) {
		jet0Idx = ijet;
	    } else {
	    if (abs(hardware::DeltaPhi(phi[jet0Idx], phi[ijet])) > M_PI/2) {
		jet1Idx = ijet;
		break;
	    }
	    }
	}
    }
    return {jet0Idx,jet1Idx};
}

RVec<int> PickDijets(RVec<float> pt, RVec<float> eta, RVec<float> phi, RVec<float> mass) {
    int jet0Idx = -1;
    int jet1Idx = -1;
    for (int ijet = 0; ijet < pt.size(); ijet++) {
        if (jet1Idx == -1) {
            if (pt[ijet] > 350 && std::abs(eta[ijet]) < 2.4 && mass[ijet] > 50) {
                if (jet0Idx == -1) {
                    jet0Idx = ijet;
                } else {
                    if (abs(hardware::DeltaPhi(phi[jet0Idx], phi[ijet])) > M_PI/2) {
                        jet1Idx = ijet;
                        break;
                    }
                }
            }
        }       
    }
    return {jet0Idx,jet1Idx};
}

std::vector<int> PickTop(RVec<float> mass, RVec<float> tagScore, RVec<int> idxs, std::pair<float,float> massCut, float scoreCut, bool invertScore=false) {
    if (idxs.size()>2) {
        std::cout << "PickTop -- WARNING: You have input more than two indices. Only two accepted. Assuming first two indices.";
    }
    std::vector<int> out(2);
    float WP = scoreCut;

    int idx0 = idxs[0];
    int idx1 = idxs[1];
    bool isTop0, isTop1;
    if (!invertScore) {
        isTop0 = (mass[idx0] > massCut.first) && (mass[idx0] < massCut.second) && (tagScore[idx0] > WP);
        isTop1 = (mass[idx1] > massCut.first) && (mass[idx1] < massCut.second) && (tagScore[idx1] > WP);
    } else {
	// if inverted, only accept jets meeting the loose score (>0.2) and not those meeting the tight cut (< WP)
        isTop0 = (tagScore[idx0] < WP) && (0.2 < tagScore[idx0]);
	isTop1 = (tagScore[idx1] < WP) && (0.2 < tagScore[idx1]);
    }

    if (isTop0 && isTop1) {
        if (tagScore[idx0] > tagScore[idx1]) {
            out[0] = idx0;
            out[1] = idx1;
        } else {
            out[0] = idx1;
            out[1] = idx0;
        }
    } else if (isTop0) {
        out[0] = idx0;
        out[1] = idx1;
    } else if (isTop1) {
        out[0] = idx1;
        out[1] = idx0;
    } else {
        out[0] = -1;
        out[1] = -1;
    }
    return out;
}

std::vector<int> PickTopCRv2(RVec<float> mass, RVec<float> tagScore, RVec<float> HiggsScore, RVec<int> idxs, std::pair<float,float> massCut, float scoreCut, bool invertScore=false) {
    if (idxs.size() > 2) {
	std::cout << "PickTop -- WARNING: You have input more than two indices. Only two accepted. Assuming first two indices.";
    }
    std::vector<int> out(2);
    float WP = scoreCut;
    int idx0 = idxs[0];
    int idx1 = idxs[1];
    bool isTop0, isTop1;
    if (!invertScore) {	// signal region - apply mass window cut and top tag reqirement
        isTop0 = (mass[idx0] > massCut.first) && (mass[idx0] < massCut.second) && (tagScore[idx0] > WP);
        isTop1 = (mass[idx1] > massCut.first) && (mass[idx1] < massCut.second) && (tagScore[idx1] > WP);
    } else {	// control region - anti-top tag and Higgs veto on the top jet
	// same as CR_v1, but also require the top candidate jet to have Higgs tag < loose WP
	// NEW 6/7/23 - add top mass window cut to leading jet
	isTop0 = (tagScore[idx0] < WP) && (0.2 < tagScore[idx0]) && (HiggsScore[idx0] < 0.2) && (mass[idx0]>150) && (mass[idx0]<200);
        isTop1 = (tagScore[idx1] < WP) && (0.2 < tagScore[idx1]) && (HiggsScore[idx1] < 0.2);
    }
    if (isTop0 && isTop1) {	// if both jets meet top (anti)tag, then choose the one with higher top score as top jet
        if (tagScore[idx0] > tagScore[idx1]) {
            out[0] = idx0;
            out[1] = idx1;
        } else {
            out[0] = idx1;
            out[1] = idx0;
        }
    // otherwise, chose the one that passed tagging to be the top candidate
    } else if (isTop0) {
        out[0] = idx0;
        out[1] = idx1;
    } else if (isTop1) {
        out[0] = idx1;
        out[1] = idx0;
    } else {
        out[0] = -1;
        out[1] = -1;
    }
    return out;
}


bool MatchToGen(int pdgID, ROOT::Math::PtEtaPhiMVector jet,
                RVec<ROOT::Math::PtEtaPhiMVector> GenPart_vect,
                RVec<int> GenPart_pdgId) {
    bool found = false;
    for (int igp = 0; igp<GenPart_vect.size(); igp++) {
        if (abs(GenPart_pdgId[igp]) == pdgID) {
            if (hardware::DeltaR(jet,GenPart_vect[igp]) < 0.8) {
                found = true;
                break;
            }
        }
    }
    return found;
}

std::vector<int> PickTopGenMatch(RVec<ROOT::Math::PtEtaPhiMVector> Dijet_vect,
                                 RVec<ROOT::Math::PtEtaPhiMVector> GenPart_vect,
                                 RVec<int> GenPart_pdgId) {
    if (Dijet_vect.size()>2) {
        std::cout << "PickTopGenMatch -- WARNING: You have input more than two indices. Only two accepted. Assuming first two indices.";
    }
    int tIdx = -1;
    int hIdx = -1;
    for (int ijet = 0; ijet < 2; ijet++) {
        if (MatchToGen(6, Dijet_vect[ijet], GenPart_vect, GenPart_pdgId)) {
            tIdx = ijet;
        } else if (MatchToGen(25, Dijet_vect[ijet], GenPart_vect, GenPart_pdgId)) {
            hIdx = ijet;
        }
    }
    return {tIdx,hIdx};
}
