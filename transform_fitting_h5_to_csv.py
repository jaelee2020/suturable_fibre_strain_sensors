#!/usr/bin/env python
# coding: utf-8

import numpy as np
import h5py
import os.path
import sys

from scipy.ndimage import gaussian_filter1d as gauss
from scipy.optimize import curve_fit as fit
from scipy.optimize import minimize


def main():
    if len(sys.argv) != 2:
        print('.')
        print('.')
        print('.')
        print('Number of parameters does not add up. Please enter command e.g. like this:')
        print('python transform_h5_to_csv.py test')
        print(' ')
        print('Nothing was done')
        return -1
    
    filename = sys.argv[1]
    if filename[-3:] == '.h5':
        filename=filename[:-3]
        
    import os.path

    if not os.path.isfile(filename + '.h5'):
        print('.')
        print('.')
        print('.')
        print("The following file did not exist:")
        print(filename + '.h5')
        print(' ')
        print('Nothing was done')
        return -2

    f = h5py.File(filename + '.h5', 'r')

    t_data = np.array(f['t'])
    t_0    = np.array(f['t_0'])
    x_data = np.array(f['x_data'])
    x_data[0,:10]

    y_data = np.array(f['y_data'])

    samples    = y_data.shape[1]
    datapoints = y_data.shape[0]

    assert np.max(np.std(x_data,0)) < 1e-10
    # If this assertion catches, your x-axis changes during the experiment!

    # Gaussian blur in order to find potential approximate minima
    gauss_data = np.zeros_like(y_data)
    sigma      = 10
    print("Standard deviation for gaussian bluring: " + str(np.round(sigma*(x_data[0,1] - x_data[0,0]),3)) + " MHz")
    for i in range(y_data.shape[0]):
        gauss_data[i,:] = gauss(y_data[i,:],sigma)

    # Get all minima. Do so by looking at the change in sign of the derivative.
    # A minima needs to be below -0.2 to be relevant!
    diff_data      = gauss_data[:,1:] - gauss_data[:,:-1]
    minima         = np.zeros_like(y_data)
    minima[:,1:-1] = ((diff_data[:,:-1]<0)*1.)*((diff_data[:,1:]>0)*1.)*((y_data[:,1:-1]<-0.2)*1.)

    # Calculate here the approximal values based on the minima approach
    approx_minima = np.ones_like(y_data[:,0])*-1.
    for i in range(0,y_data.shape[0],1):
        # Get index of all the minima in ith trial
        temp_minima   = np.argwhere(minima[i,:])
        temp_minima   = np.array([temp_minima[index][0] for index in range(temp_minima.shape[0])])

        if temp_minima.shape[0]>0:
            # Get the blurred values of these minima
            values_minima = gauss_data[i,temp_minima]

            # Get the smallest minimum in case of multiple minima
            arg_smallest  = np.argmin(values_minima)

            # Get the index of the smallest minimum
            smallest_min  = temp_minima[arg_smallest]
            
            approx_minima[i] = smallest_min
        
    # Define the pdf of a Polynomial
    def poly_pdf(x,a,b,c,d,e,f):
        return a + b*x + c*(x**2) + d*(x**3) + e*(x**4) + f*(x**5)

    # Calculate now the minima based on fit around the data points from the approximal values
    slength  = 10 # Defines the region where to search for lowest point first (2*slength+1)
    dlength  = 6 # Defines how many data points to consider left and right to the minimum (2*dlength+1)

    fit_minima = np.copy(approx_minima)

    for i in range(fit_minima.shape[0]):
        approx_i = approx_minima[i]
        if approx_i>=0: # This means the minimum is relevant
            # Find first actual minima in data, since blurring shifts that peak
            lower_bound = max(approx_i-slength,0)
            upper_bound = min(approx_i+slength+1,x_data.shape[1])

            x_data_i    = np.arange(int(lower_bound),int(upper_bound))
            y_data_i    = y_data[i,int(lower_bound):int(upper_bound)]
            
            approx_i         = np.argmin(y_data_i)+lower_bound
            approx_minima[i] = approx_i # Update minimum to actual minimum
            
            lower_bound = max(approx_i-dlength,0)
            upper_bound = min(approx_i+dlength+1,x_data.shape[1])

            x_data_i    = np.arange(int(lower_bound),int(upper_bound))
            y_data_i    = y_data[i,int(lower_bound):int(upper_bound)]

            p,_ = fit(poly_pdf,x_data_i-approx_i,y_data_i)#,p0=[1,1,1,approx_i,1])
            
            
            def current_polynomial(x):
                return p[0] + p[1]*x + p[2]*(x**2) + p[3]*(x**3) + p[4]*(x**4) + p[5]*(x**5)
            
            #assert i!=2260
            
            f = minimize(current_polynomial, x0=0)
            fit_minima[i] = f.x + approx_i
        
        


        if temp_minima.shape[0]>0:
            # Get the blurred values of these minima
            values_minima = gauss_data[i,temp_minima]

            # Get the smallest minimum in case of multiple minima
            arg_smallest  = np.argmin(values_minima)

            # Get the index of the smallest minimum
            smallest_min  = temp_minima[arg_smallest]
            
            approx_minima[i] = smallest_min
            
    # Transform the fitted positions to actual frequencies
    resonant_freq = np.zeros_like(fit_minima)
    for i in range(resonant_freq.shape[0]):
        if fit_minima[i]>0:
            min_full = int(fit_minima[i]//1 + 0.5)
            min_diff = fit_minima[i]-min_full
            resonant_freq[i] = x_data[i,min_full]+min_diff*(x_data[i,min_full+1]-x_data[i,min_full])
            
    # Write data into file
    with open(filename + '.csv','w') as f:
        # Write header
        s = str(t_0)
        for i in range(samples):
            s += ',' + str(x_data[0,i])
        s += ',f0'
        f.write(s)
        f.write('\n')

        for j in range(datapoints):
            s = str(t_data[j])
            for i in range(samples):
                s += ',' + str(y_data[j,i])
            s += ',' + str(resonant_freq[j])
            f.write(s)
            f.write('\n')

if __name__ == "__main__":
    main()
