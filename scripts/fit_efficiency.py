import ROOT
from array import array 
import numpy as np 

f_17 = ROOT.TFile.Open('THtrigger2D_HT750_17.root','READ')
hist17 = f_17.Get('Pretag_hist')
eff17 = f_17.Get('Pretag')
func17 = ROOT.TF2("eff_func","1-[0]/10*exp([1]*y/1000)*exp([2]*x/200)",60,560,800,3500)
func17.SetParameters(25.,-3.,-1.)
r17 = hist17.Fit(func17,'S')

def createTriggerShape(h, func, resultPtr, name, nBinsX=50, nBinsY=50):
    '''creates the trigger uncertainty histogram +-uncertainty '''
    # Get the histogram dimensions from the efficiency (which is used in the ML fit, so we want it to match)
    xMin = h.GetXaxis().GetXmin()
    xMax = h.GetXaxis().GetXmax()
    yMin = h.GetYaxis().GetXmin()
    yMax = h.GetYaxis().GetXmax()
    # Now create a blank histogram with finer binning so we can get the most accurate representation of uncertainties.
    nBinsX = nBinsX
    nBinsY = nBinsY
    hNew = ROOT.TH2F(name,name,nBinsX,xMin,xMax,nBinsY,yMin,yMax)
    
    # first get (x,y) bin in 2D coords (1,1)->(nBinsX,nBinsY)
    for x in range(1, nBinsX+1):
        for y in range(1, nBinsY+1):
            # Now get (x,y) in physics coords (xMin,yMin)->(xMax,yMax)
            xPhys = xMin + (x-1)*((xMax-xMin)/nBinsX)
            yPhys = yMin + (y-1)*((yMax-yMin)/nBinsY)
            # calculate f(x,y) +/- error 
            val = func.Eval(xPhys,yPhys)
            ci = array('d',[0.0])
            points = array('d',[xPhys,yPhys])
            resultPtr.GetConfidenceIntervals(1, 2, 1, points, ci, 0.683, False)
            # set histogram bin content and error
            hNew.SetBinContent(x,y,val)
            hNew.SetBinError(x,y,ci[0])
            
    resultPtr.Delete()
    
    f = ROOT.TFile.Open("TEST_{}.root".format(name),'RECREATE')
    hNew.Write()
    f.Close()

createTriggerShape(hist17, func17, r17, 'test17')

