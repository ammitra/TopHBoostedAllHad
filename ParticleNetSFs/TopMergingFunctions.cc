#include <TFile.h>
#include <TMath.h>
#include <stdio.h>
#include <vector>
#include <iostream>
#include "ROOT/RVec.hxx"
#include "TIMBER/Framework/include/common.h"

using namespace ROOT::VecOps;
using rvec_i = RVec<int>;
using rvec_f = RVec<float>;
using rvec_c = RVec<char>;
using rvec_b = RVec<bool>;

Float_t deltaR(Float_t eta1, Float_t phi1, Float_t eta2, Float_t phi2);
Int_t probeAK8JetIdx(Int_t nFatJet,rvec_f FatJet_pt,rvec_f FatJet_msoftdrop,rvec_f FatJet_phi,rvec_f FatJet_eta, rvec_i FatJet_jetId,Float_t lPhi,Float_t lEta);
Int_t classifyProbeJet(Int_t fatJetIdx,rvec_f FatJet_phi,rvec_f FatJet_eta, Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother);
Int_t bFromTopinJet(Float_t FatJet_phi, Float_t FatJet_eta,Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother );
Int_t bFromTopBothinJet(Float_t FatJet_phi, Float_t FatJet_eta,Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother );
Int_t qFromWInJet(Float_t FatJet_phi, Float_t FatJet_eta,Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother );
Int_t qqFromWAllInJet(Float_t FatJet_phi, Float_t FatJet_eta,Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother );


Float_t deltaR(Float_t eta1, Float_t phi1, Float_t eta2, Float_t phi2){
    Float_t deltaEta      = eta2-eta1;
    Float_t deltaPhi_corr = hardware::DeltaPhi(phi1,phi2);//if |phi1-phi2|>pi, reduce it by pi
    Float_t deltaR        = TMath::Sqrt(deltaEta*deltaEta+deltaPhi_corr*deltaPhi_corr);
    return deltaR;
}

Int_t bFromTopinJet(Float_t FatJet_phi, Float_t FatJet_eta,Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother ){
    for(Int_t i=0; i<nGenPart;i++){
        Int_t pid = GenPart_pdgId[i];
        Int_t motherIdx = GenPart_genPartIdxMother[i];
        Int_t motherPid = GenPart_pdgId[motherIdx];

        if(motherPid==-1){
            continue;
        }

        Float_t dR = deltaR(GenPart_eta[i],GenPart_phi[i],FatJet_eta,FatJet_phi);

        if(TMath::Abs(pid)==5 && TMath::Abs(motherPid)==6 && dR<0.8){
            return 1;
        }
    }
    return 0;
}



Int_t bFromTopBothinJet(Float_t FatJet_phi, Float_t FatJet_eta,Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother ){
    for(Int_t i=0; i<nGenPart;i++){
        Int_t pid = GenPart_pdgId[i];
        Int_t motherIdx = GenPart_genPartIdxMother[i];
        Int_t motherPid = GenPart_pdgId[motherIdx];

        if(motherPid==-1){
            continue;
        }

        Float_t dR = deltaR(GenPart_eta[i],GenPart_phi[i],FatJet_eta,FatJet_phi);
        Float_t dRMother = deltaR(GenPart_eta[motherIdx],GenPart_phi[motherIdx],FatJet_eta,FatJet_phi);

        if(TMath::Abs(pid)==5 && TMath::Abs(motherPid)==6 && dR<0.8 && dRMother<0.8){
            return 1;
        }
    }
    return 0;
}

Int_t qFromWInJet(Float_t FatJet_phi, Float_t FatJet_eta,Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother ){
    for(Int_t i=0; i<nGenPart;i++){
        Int_t pid = GenPart_pdgId[i];
        Int_t motherIdx = GenPart_genPartIdxMother[i];
        Int_t motherPid = GenPart_pdgId[motherIdx];

        if(motherPid==-1) {
            continue;
        }

        Float_t dR = deltaR(GenPart_eta[i],GenPart_phi[i],FatJet_eta,FatJet_phi);
        if(dR<0.8 && TMath::Abs(pid)<6 && TMath::Abs(pid)>0 && TMath::Abs(motherPid)==24){
            return 1;
        }
    }
    return 0;
}

Int_t qqFromWAllInJet(Float_t FatJet_phi, Float_t FatJet_eta,Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother ){
    Int_t nQ = 0;
    Int_t isWInJet = 0;
    for(Int_t i=0; i<nGenPart;i++){
        Int_t pid = GenPart_pdgId[i];
        Int_t motherIdx = GenPart_genPartIdxMother[i];
        Int_t motherPid = GenPart_pdgId[motherIdx];

        if(motherPid==-1){
            continue;
        }

        Float_t dR = deltaR(GenPart_eta[i],GenPart_phi[i],FatJet_eta,FatJet_phi);
        Float_t dRMother = deltaR(GenPart_eta[motherIdx],GenPart_phi[motherIdx],FatJet_eta,FatJet_phi);
        if(dR<0.8 && TMath::Abs(pid)<6 && TMath::Abs(pid)>0 && TMath::Abs(motherPid)==24 && dRMother<0.8){
            nQ = nQ+1;
            isWInJet = isWInJet+1;
        }
    }
    if(nQ>1 && isWInJet>1){
        return 1;
    }
    else{
        return 0;
    }
}

Int_t isJetW(Float_t FatJet_phi, Float_t FatJet_eta,Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother) {
    // 1: jet is matched to W (not from top decay), 0: jet is not matched to gen W
    Int_t nW = 0;
    for (Int_t i=0; i<nGenPart; i++) {
	Int_t pid = GenPart_pdgId[i];
	Int_t motherIdx = GenPart_genPartIdxMother[i];
        Int_t motherPid = GenPart_pdgId[motherIdx];
	// ensure mother is not a top, or another W 
        if(motherPid==-1 || TMath::Abs(pid)!=24 || TMath::Abs(motherPid)==6){
            continue;
        }
	// deltaR with FatJet
	Float_t dR = deltaR(GenPart_eta[i],GenPart_phi[i],FatJet_eta,FatJet_phi);
	if (dR<0.8 && TMath::Abs(pid)==24) {
	    nW++;
	}
    }
    if (nW > 0) {
	return 1;
    }
    else {
	return 0;
    }
};

Int_t isJetH(Float_t FatJet_phi, Float_t FatJet_eta,Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother) {
    // 1: jet is matched to H (not from top decay), 0: jet is not matched to gen H
    Int_t nH = 0;
    for (Int_t i=0; i<nGenPart; i++) {
        Int_t pid = GenPart_pdgId[i];
        Int_t motherIdx = GenPart_genPartIdxMother[i];
        Int_t motherPid = GenPart_pdgId[motherIdx];
        if(motherPid==-1){
            continue;
        }
        // deltaR with FatJet
        Float_t dR = deltaR(GenPart_eta[i],GenPart_phi[i],FatJet_eta,FatJet_phi);
        if (dR<0.8 && TMath::Abs(pid)==25) {
            nH++;
        }
    }
    if (nH > 0) {
        return 1;
    }
    else {
        return 0;
    }
};

Int_t classifyProbeJet(Int_t fatJetIdx,rvec_f FatJet_phi,rvec_f FatJet_eta, Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother){
//1: qq, 2: bq, 3:bqq, 4:Higgs, 5:W(not from top), 0:other
Int_t btInJet = bFromTopinJet(FatJet_phi[fatJetIdx],FatJet_eta[fatJetIdx],nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother);
Int_t bInJet = bFromTopBothinJet(FatJet_phi[fatJetIdx],FatJet_eta[fatJetIdx],nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother);
Int_t qInJet = qFromWInJet(FatJet_phi[fatJetIdx],FatJet_eta[fatJetIdx],nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother);
Int_t qqWInJet = qqFromWAllInJet(FatJet_phi[fatJetIdx],FatJet_eta[fatJetIdx],nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother);
Int_t isW = isJetW(FatJet_phi[fatJetIdx],FatJet_eta[fatJetIdx],nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother);
Int_t isH = isJetH(FatJet_phi[fatJetIdx],FatJet_eta[fatJetIdx],nGenPart,GenPart_phi,GenPart_eta,GenPart_pdgId,GenPart_genPartIdxMother);

    if(btInJet && qqWInJet){
        return 3;
    }
    else if(bInJet && qInJet){
        return 2;
    }
    else if(qqWInJet){
        return 1;
    }
    else{	// check if jet is Higgs or W (not from top)
	if (isH && !isW) {
	    return 4;
	}
	else if (!isH && isW) {
	    return 5;
	}
	else {
            return 0;

	}
    }
}

RVec<Int_t> classifyProbeJets(RVec<Int_t> fatJetIdxs, rvec_f FatJet_phi,rvec_f FatJet_eta, Int_t nGenPart, rvec_f GenPart_phi,rvec_f GenPart_eta, rvec_i GenPart_pdgId, rvec_i GenPart_genPartIdxMother) {
    RVec<Int_t> out(2);
    for (Int_t iJet : fatJetIdxs) {
	Int_t status = classifyProbeJet(iJet, FatJet_phi, FatJet_eta, nGenPart, GenPart_phi, GenPart_eta, GenPart_pdgId, GenPart_genPartIdxMother);
	out[iJet] = status;
    }
    return out;
}

Int_t probeAK8JetIdx(Int_t nFatJet,rvec_f FatJet_pt,rvec_f FatJet_msoftdrop,rvec_f FatJet_phi,rvec_f FatJet_eta, rvec_i FatJet_jetId,Float_t lPhi,Float_t lEta){
    for(Int_t i=0; i<nFatJet;i++){
        Int_t fatJetReq = FatJet_pt[i]>350 && FatJet_msoftdrop[i]>30 && FatJet_jetId[i]>1;
        Float_t dR = deltaR(FatJet_eta[i],FatJet_phi[i],lEta,lPhi);//opposite hemisphere of the lepton
        if(fatJetReq && dR>2.0){
            return i;
        }
    }
    return -1;
}
