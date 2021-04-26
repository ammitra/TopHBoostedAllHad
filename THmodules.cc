#include "ROOT/RVec.hxx"
#include "TIMBER/Framework/include/common.h"

using namespace ROOT::VecOps;

RVec<int> PickDijets(RVec<float> pt, RVec<float> eta, RVec<float> phi, RVec<float> mass) {
    int jet0Idx = -1;
    int jet1Idx = -1;
    for (int ijet = 0; ijet < pt.size(); ijet++) {
        if (jet1Idx == -1) {
            if (pt[ijet] > 350 && std::abs(eta[ijet]) < 2.4 && mass[ijet] > 50) {
                if (jet0Idx == -1) {
                    jet0Idx = ijet;
                } else {
                    if (hardware::DeltaPhi(phi[jet0Idx], phi[ijet]) > M_PI/2) {
                        jet1Idx = ijet;
                        break;
                    }
                }
            }
        }       
    }
    return {jet0Idx,jet1Idx};
}

std::vector<int> PickTop(RVec<float> mass, RVec<float> tagScore, RVec<int> idxs, bool invertScore=false) {
    if (idxs.size()>2) {
        std::cout << "PickTop -- WARNING: You have input more than two indices. Only two accepted. Assuming first two indices.";
    }
    std::vector<int> out(2);
    float WP = 0.632;

    int idx0 = idxs[0];
    int idx1 = idxs[1];
    bool isTop0, isTop1;
    if (!invertScore) {
        isTop0 = (mass[idx0] > 105) && (mass[idx0] < 210) && (tagScore[idx0] > WP);
        isTop1 = (mass[idx1] > 105) && (mass[idx1] < 210) && (tagScore[idx1] > WP);
    } else {
        isTop0 = (mass[idx0] > 105) && (mass[idx0] < 210) && (tagScore[idx0] < WP);
        isTop1 = (mass[idx1] > 105) && (mass[idx1] < 210) && (tagScore[idx1] < WP);
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