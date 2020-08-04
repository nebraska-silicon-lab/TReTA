{
  auto c1 = new TCanvas("c1","Thermal Conductivity: Glass",200,10,700,500);
  //c1->SetFillColor(42);
  //c1->SetGrid();
  //c1->GetFrame()->SetFillColor(21);
  c1->GetFrame()->SetBorderSize(12);
  // const Int_t n = 4;
  // Double_t y[n]  = {1.32,2.77,3.94,6.011}; // power*l/A
  // Double_t x[n]  = {1.65,3.56,5.1,8.07};  // delta T
  // Double_t ey[n] = {0.00025, 0.00025, 0.00025, 0.00025};
  // Double_t ex[n] = {0.5, 0.5, 0.5, 0.5};

  //AlN
  const Int_t n = 3;
  Double_t y[n]  = {2.38,4.15,8.28}; // power*l/A
  Double_t x[n]  = {0.43,0.88,1.8};  // delta T
  Double_t ey[n] = {0.0004, 0.0004, 0.0004,};
  Double_t ex[n] = {0.5, 0.5, 0.5};


  
  auto gr = new TGraphErrors(n,x,y,ex,ey);
  //gr->SetTitle("Thermal Conductivity: Glass");
  gr->SetTitle("Thermal Conductivity: AlN"); 
  gr->SetMarkerColor(4);
  gr->SetMarkerStyle(21);
  gr->GetXaxis()->SetTitle("T_{hot}-T_{cold} ");
  gr->GetYaxis()->SetTitle("Power*L/A");
  gr->Draw("AP");
  
}
