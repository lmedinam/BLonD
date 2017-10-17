
# Copyright 2016 CERN. This software is distributed under the
# terms of the GNU General Public Licence version 3 (GPL Version 3), 
# copied verbatim in the file LICENCE.md.
# In applying this licence, CERN does not waive the privileges and immunities 
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.
# Project website: http://blond.web.cern.ch/

'''
Example input for simulation with RF noise
No intensity effects
'''

from __future__ import division, print_function
from builtins import range
import numpy as np
from input_parameters.ring import Ring
from input_parameters.rf_parameters import RFStation
from trackers.tracker import RingAndRFTracker
from beam.beam import Beam, Proton
from beam.distributions import bigaussian
from beam.profile import CutOptions, Profile, FitOptions
from monitors.monitors import BunchMonitor
from plots.plot import Plot
from llrf.rf_noise import FlatSpectrum



# Simulation parameters --------------------------------------------------------
# Bunch parameters
N_b = 1.e9           # Intensity
N_p = 50001          # Macro-particles
tau_0 = 0.4e-9          # Initial bunch length, 4 sigma [s]

# Machine and RF parameters
C = 26658.883        # Machine circumference [m]
p_s = 450.e9         # Synchronous momentum [eV]
h = 35640            # Harmonic number
V = 6e6             # RF voltage [eV]
dphi = 0             # Phase modulation/offset
gamma_t = 55.759505  # Transition gamma
alpha = 1./gamma_t/gamma_t        # First order mom. comp. factor

# Tracking details
N_t = 200         # Number of turns to track
dt_plt = 20        # Time steps between plots

# Simulation setup -------------------------------------------------------------
print("Setting up the simulation...")
print("")

# Define general parameters
general_params = Ring(N_t, C, alpha, p_s, Proton())

# Define RF station parameters and corresponding tracker
rf_params = RFStation(general_params, 1, [h], [V], [0])

# Pre-processing: RF phase noise -----------------------------------------------
RFnoise = FlatSpectrum(general_params, rf_params, delta_f = 1.12455000e-02, fmin_s0 = 0, 
                       fmax_s0 = 1.1, seed1=1234, seed2=7564, 
                       initial_amplitude = 1.11100000e-07, folder_plots =
                       '../output_files/EX3_fig')
RFnoise.generate()
rf_params.phi_noise = np.array(RFnoise.dphi, ndmin =2) 


print("   Sigma of RF noise is %.4e" %np.std(RFnoise.dphi))
print("   Time step of RF noise is %.4e" %RFnoise.t[1])
print("")


beam = Beam(general_params, N_p, N_b)
long_tracker = RingAndRFTracker(rf_params, beam)

print("General and RF parameters set...")


# Define beam and distribution

# Generate new distribution
bigaussian(general_params, rf_params, beam, tau_0/4, 
                              reinsertion = True, seed=1)

print("Beam set and distribution generated...")


# Need slices for the Gaussian fit; slice for the first plot
slice_beam = Profile(beam, CutOptions(n_slices=100),
                 FitOptions(fit_option='gaussian'))        
slice_beam.track()
# Define what to save in file
bunchmonitor = BunchMonitor(general_params, rf_params, beam, '../output_files/EX3_output_data', Profile=slice_beam)


# PLOTS

format_options = {'dirname': '../output_files/EX3_fig', 'linestyle': '.'}
plots = Plot(general_params, rf_params, beam, dt_plt, N_t, 0, 
             0.0001763*h, -450e6, 450e6, xunit= 'rad',
             separatrix_plot= True, Profile = slice_beam, h5file = '../output_files/EX3_output_data', 
             histograms_plot = True, format_options = format_options)

# Accelerator map
map_ = [long_tracker] + [slice_beam] + [bunchmonitor] + [plots]
print("Map set")
print("")


# Tracking ---------------------------------------------------------------------
for i in range(1,N_t+1):
    
    
    # Plot has to be done before tracking (at least for cases with separatrix)
    if (i % dt_plt) == 0:
        
        print("Outputting at time step %d..." %i)
        print("   Beam momentum %.6e eV" %beam.momentum)
        print("   Beam gamma %3.3f" %beam.gamma)
        print("   Beam beta %3.3f" %beam.beta)
        print("   Beam energy %.6e eV" %beam.energy)
        print("   Four-times r.m.s. bunch length %.4e [s]" %(4.*beam.sigma_dt))
        print("   Gaussian bunch length %.4e [s]" %slice_beam.bunchLength)
        print("")
        

    # Track
    for m in map_:
        m.track()
        
        
    # Define losses according to separatrix and/or longitudinal position
    beam.losses_separatrix(general_params, rf_params)
    beam.losses_longitudinal_cut(0., 2.5e-9)

print("Done!")
print("")
