from ROOT import TFile,TCanvas,TIter,TH1,TH2,TH1F,TDirectory,TLegend

import os,sys

#first = True
ratios = False
first = {}

def plot_hist(h):
    h.SetStats(0)
    h.Draw()

def plot_2dhist(h):
    h.SetStats(0)
    h.Draw("COLZ")

def plot_ratio_hist(h):
    h.SetStats(0)
    h.GetYaxis().SetRangeUser(0.75, 1.2)
    h.Draw()

def plot_overlay_hist(h):
    h.SetStats(0)
    h.SetLineWidth(2)
    h.SetLineColor(4)
    h.Draw("SAME")


def PlotHistsRecursive(the_dir, path, level, pdf_fname):
    level += 1
    # loop over all keys in the current directory, ROOT-style
    key_iter = TIter(the_dir.GetListOfKeys())
    key = key_iter()

    if(level == 2):
        pdf_fname = the_dir.GetName()
        first[pdf_fname] = True

    while( key ):
        obj = key.ReadObj()
        obj_pathname = path+"/"+key.GetName()

        c1.Clear()

        # if the object is a histogram, then see if we should plot it
        if(isinstance(obj,TH1)):
            print "plotting " + obj_pathname
            obj.SetTitle(obj_pathname)
            h2 = f2.Get(obj_pathname)
            h2.SetTitle(obj_pathname)

            # plot histogram
            if(isinstance(obj,TH2)):
                obj.SetTitle(obj_pathname + " - HG3")
                h2.SetTitle(obj_pathname + " - HG4")
                c1.Divide(1,2)
                c1.cd(1)
                plot_2dhist(obj)
                c1.cd(2)
                plot_2dhist(h2)

                # save image to disk
                if first[pdf_fname] == True:
                    c1.Print(pdf_fname+".pdf(")
                else:
                    c1.Print(pdf_fname+".pdf")

                key = key_iter()
                continue
            #    self.plot_2dhist(obj)
            #else:
            #    self.plot_hist(obj)


            #obj.Rebin()
            #h2.Rebin()

            plot_hist(obj)
            plot_overlay_hist(h2)

            leg = TLegend(0.72,0.77,0.9,0.9)
            leg.AddEntry(obj,"hdgeant","l")
            leg.AddEntry(h2,"hdgeant4","l")
            leg.Draw()

            # save image to disk
            if first == True:
                c1.Print(pdf_fname+".pdf(")
            else:
                c1.Print(pdf_fname+".pdf")
                
            if ratios == True:
                h1f = TH1F(obj)
                h2f = TH1F(h2) 
                h1f.Divide(h2f)
                plot_ratio_hist(h1f)


                c1.Print("out.pdf")
            
        # if the object is a directory, access what's inside
        if(isinstance(obj, TDirectory)):
            PlotHistsRecursive(obj, obj_pathname, level, pdf_fname)

        # END OF LOOP - move to next item in the directory
        key = key_iter()
    del key_iter


c1 = TCanvas("c1", "c1", 800, 600)

f1 = TFile(sys.argv[1])
f2 = TFile(sys.argv[2])

BASE_DIRECTORY = "Independent"
if len(sys.argv)>3:
    BASE_DIRECTORY = sys.argv[3]

d = f1.Get(BASE_DIRECTORY)
d.ls()
PlotHistsRecursive(d, "/"+BASE_DIRECTORY, 0, "out")

#c1.Print("out.pdf)")
for fname in first.keys():
    c1.Print(fname+".pdf]")
