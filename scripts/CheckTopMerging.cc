#include "Math/Vector4Dfwd.h"
#include "../TIMBER/TIMBER/Framework/include/GenMatching.h"
#include <iostream>

using LVector = ROOT::Math::PtEtaPhiMVector;
using rvec_i = RVec<Int_t>;

struct GenPartStruct {
        Int_t status;
        Float_t phi;
        Int_t statusFlags;
        Float_t pt;
        Int_t pdgId;
        Float_t eta;
        Float_t mass;
        Int_t genPartIdxMother;

	GenPartStruct() = default;
        GenPartStruct(Int_t status,Float_t phi,Int_t statusFlags,Float_t pt,Int_t pdgId,Float_t eta,Float_t mass,Int_t genPartIdxMother) :
        status(status),phi(phi),statusFlags(statusFlags),pt(pt),pdgId(pdgId),eta(eta),mass(mass),genPartIdxMother(genPartIdxMother) {};
};

RVec<GenPartStruct> make_GenPart_vec(
	Int_t number,
	RVec<Int_t> status, 
	RVec<Float_t> phi,
	RVec<Int_t> status_flags,
	RVec<Float_t> pt,
	RVec<Int_t> pdgID, 
	RVec<Float_t> eta,
	RVec<Float_t> mass,
	RVec<Int_t> mother) {

	RVec<GenPartStruct> _out;
	_out.reserve(number);
	for (size_t i=0; i < number; i++) {
	    GenPartStruct gps(status[i],phi[i],status_flags[i],pt[i],pdgID[i],eta[i],mass[i],mother[i]);
	    _out.emplace_back(gps);
	    //_out.emplace_back(status[i],phi[i],status_flags[i],pt[i],pdgID[i],eta[i],mass[i],mother[i]);
	}
	return _out;
}

Float_t getPartIdx(Int_t nGenPart, rvec_i GenPart_pdgId, rvec_i GenPart_statusFlags, Int_t pdgId){
    //returns idx of the first hard process parton with GenPart_pdgId == pdgId, -1 otherwise
    // statusFlags bit 7 : isHardProcess, bit counting starts from zero!
    for(Int_t i=0;i<nGenPart;i++){
        if(GenPart_pdgId[i]==pdgId && (GenPart_statusFlags[i]&(1 << 7))){
            return i;
        }
    }
    return -1;    
}

/* -------------------------------------------------------------------------
 * Look at reconstructed top quark, and determine whether it belongs to:
 * 	- 0	(0, non-merged)
 * 	- b	(1, b-only)
 * 	- bq 	(2, partial merge)
 * 	- qq	(3, W-merged)
 * 	- bqq+	(4, fully-merged)
 */
template <class T>
int TopSplitting(LVector top_vect, T GenParts) {
    // Get the numbers of b and q (from W)
    int nmerged  = 0;	// general number of merged, matched, particles
    int	nbquarks = 0;	// number of b quarks matched to the top vect (0 or 1)
    int nWquarks = 0;	// number of quarks from the top-matched W, matched to the top vect
    int nmerged_b = 0;  // number of MERGED b quarks from top decay
    int nmerged_q = 0;  // number of MERGED light quarks from top-matched W decay
    int status;		// status of the top-merging, as defined above
    // set up the Particle containers
    GenParticleTree GPT(GenParts.size());
    RVec<Particle*> Ws, quarks, bprongs, wqprongs;
    // fill the tree
    int this_pdgId;
    for (size_t i = 0; i < GenParts.size(); i++) {
	Particle* this_particle = GPT.AddParticle(Particle(i,GenParts[i]));
	this_pdgId = this_particle->pdgId;
	if (abs(this_pdgId) == 24) {
	    Ws.push_back(this_particle);
	}
	else if (abs(this_pdgId) >= 1 && abs(this_pdgId) <= 5) {
	    quarks.push_back(this_particle);
	}
    }
    // from the quarks, identify the top-matched bottom quark
    Particle *q, *bottom_parent;
    for (size_t iq = 0; iq < quarks.size(); iq++) {
	q = quarks[iq];
	if (abs(q->pdgId) == 5) {  // bottom
	    std::cout << "b quark found\n";
            if (bottom_parent->flag != false) { // if has parent
		// if parent is the matched top (pdgId=top && R<0.8 from top_vect)
		std::cout << "b quark has parent\n";
		/*
		if (abs(bottom_parent->pdgId) == 6 && bottom_parent->DeltaR(top_vect) < 0.8) {
		    nbquarks += 1;	  // ID'd b quark from the matched top, not sure if its merged
		    bprongs.push_back(q);
		    std::cout << "top-matched b quark found\n";
		}
		*/
		if (abs(bottom_parent->pdgId) == 6) { std::cout << "b quark parent is top\n"; }
		else { std::cout << "b quark parent is " << bottom_parent->pdgId << "\n"; }
		if (bottom_parent->DeltaR(top_vect) < 0.8) { std::cout << "b quark parent is aligned with jet\n"; }
		else { std::cout << "b quark parent has DeltaR = " << bottom_parent->DeltaR(top_vect) << "\n"; }
	    }
	}
    }
    // now look for the W from matched top, see if its daughters are valid
    Particle *W, *this_W, *wChild, *wParent;
    std::vector<Particle*> this_W_children;
    for (size_t iW = 0; iW < Ws.size(); iW++) {
	W = Ws[iW];
	wParent = GPT.GetParent(W);
	if (wParent->flag != false) { // has parent
	    // make sure W is matched to the top (pdgId=top && R<0.8 from top_vect)
	    if (abs(wParent->pdgId) == 6 && wParent->DeltaR(top_vect) < 0.8) {
		this_W = W;
		this_W_children = GPT.GetChildren(this_W);
		// Make sure the child is not just another W
		if ((this_W_children.size() == 1) && (this_W_children[0]->pdgId == W->pdgId)) {
                    this_W = this_W_children[0];
                    this_W_children = GPT.GetChildren(this_W);
		}
		// check the daughter particles
		for (size_t ichild = 0; ichild < this_W_children.size(); ichild++) {
		    wChild = this_W_children[ichild];
		    int child_pdgId = wChild->pdgId;
		    if (abs(child_pdgId) >= 1 && abs(child_pdgId) <= 5) {
			nWquarks += 1;
			wqprongs.push_back(wChild);
		    }
		}
	    }
	}
    }
    // now loop over everything and check merged status
    // first check b quarks directly from (matched) top decay
    for (int ib = 0; ib < bprongs.size(); ib++) {
	if (bprongs[ib]->DeltaR(top_vect) < 0.8) {   // top-matched b is merged
	    nmerged += 1;	// general merged particles
	    nmerged_b += 1;
	    std::cout << "top-matched b-quark is merged w jet\n";
	}
    }
    // now check quarks from decay of top-matched W
    for (int iq = 0; iq < wqprongs.size(); iq++) {
	if (wqprongs[iq]->DeltaR(top_vect) < 0.8) {  // top-matched Wq is merged
	    nmerged += 1;
	    nmerged_q += 1;
	}
    }
    // calculate the final status
    // 	- 0     (0, non-merged)
    // 	- b     (1, b-only)
    // 	- q	(2, q from W merged only)
    // 	- bq    (3, partial merge)
    //  - qq    (4, W-merged)
    //  - bqq+  (5, fully-merged)

    /*
    std::cout << "nmerged: " << nmerged << "\n";
    std::cout << "nmerged q: " << nmerged_q << "\n";
    std::cout << "nmerged b: " << nmerged_b << "\n";
    */

    if (nmerged == 0) {
	status = 0;
    }
    else if (nmerged == 1) {
	if (nmerged_b >= 1) { 
	    status = 1;
	}
	else if (nmerged_q >= 1) {
	    status = 2;
	}
	else { status = -1; }
    }
    else if (nmerged == 2) {
	if (nmerged_b == 1 && nmerged_q == 1) {
	    status = 3;
	}
	else if (nmerged_q == 2) {
	    status = 4;
	}
	else { status = -1; }
    }
    else if (nmerged == 3) {
	if (nmerged_b >= 1 && nmerged_q >= 2) {
	    status = 5;
	}
        else { status = -1; }
    }
    else if (nmerged > 3) {
	if (nmerged_b >= 1 && nmerged_q >= 2) {
	    status = 5;
	}
        else { status = -1; }
    }
    else {
	status = -1;
    }
    return status;
}


template <class T>
int NMerged(LVector top_vect, T GenParts) {
    // Final number of quarks merged inside the reconstructed jet
    int nmerged = 0;
    // prongs are final particles we check
    GenParticleTree GPT(GenParts.size());
    RVec<Particle*> Ws, quarks, prongs;
    // now start filling in the tree
    int this_pdgId;
    for (size_t i = 0; i < GenParts.size(); i++) {
    	Particle* this_particle = GPT.AddParticle(Particle(i,GenParts[i])); // add particle to tree
    	this_pdgId = this_particle->pdgId;
    	if (abs(this_pdgId) == 24) {
            Ws.push_back(this_particle);
    	} else if (abs(this_pdgId) >= 1 && abs(this_pdgId) <= 5) {
            quarks.push_back(this_particle);
    	}
    }
    // with tree built and all Ws and non-top quarks tracked, look for the bototm quark (from matching top)
    Particle *q, *bottom_parent;
    for (size_t iq = 0; iq < quarks.size(); iq++) {
    	q = quarks[iq];
    	if (abs(q->pdgId) == 5) { // if bottom
            bottom_parent = GPT.GetParent(q);
            if (bottom_parent->flag != false) { // if has parent
            	// if parent is a matched top
            	if (abs(bottom_parent->pdgId) == 6 && bottom_parent->DeltaR(top_vect) < 0.8) { 
                    prongs.push_back(q);
            	}
            }
    	}
    }
    // Now look for W (from matching top) and get daughter quarks
    Particle *W, *this_W, *wChild, *wParent;
    std::vector<Particle*> this_W_children;
    for (size_t iW = 0; iW < Ws.size(); iW++) {
    	W = Ws[iW];
    	wParent = GPT.GetParent(W);
    	if (wParent->flag != false) {
            // Make sure parent is top that's in the jet
            if (abs(wParent->pdgId) == 6 && wParent->DeltaR(top_vect) < 0.8) {
            	this_W = W;
            	this_W_children = GPT.GetChildren(this_W);
            	// Make sure the child is not just another W
            	if ((this_W_children.size() == 1) && (this_W_children[0]->pdgId == W->pdgId)) {
                    this_W = this_W_children[0];
                    this_W_children = GPT.GetChildren(this_W);
            	}
            	// Add children as prongs
            	for (size_t ichild = 0; ichild < this_W_children.size(); ichild++) {
                    wChild = this_W_children[ichild];
                    int child_pdgId = wChild->pdgId;
                    if (abs(child_pdgId) >= 1 && abs(child_pdgId) <= 5) {
                    	prongs.push_back(wChild);
                    }
            	} 
            }
    	}
    }
    // Finally, check how many of the prongs found are within radius of the jet and return
    for (int iprong = 0; iprong < prongs.size(); iprong++) {
    	if (prongs[iprong]->DeltaR(top_vect) < 0.8) {
            nmerged++;
    	}
    }
    // Enforce that any more than three prongs also be considered a "merged" top
    return std::min(nmerged,3);
}
