import numpy as np
import matplotlib.pyplot as plt
import sys
import scipy as sp
from scipy import stats
import os
import configparser
import csv


def find_streak(cap_vs_volt, start_index, diff_threshold):
    slope, y_intercept, r_value, streak_size = 0,0,0,0
    for end_index in range(start_index+3, cap_vs_volt.shape[0]):
        slope, y_intercept, r_value, _, _ = sp.stats.linregress(cap_vs_volt[start_index:end_index, :])
        pred = slope * cap_vs_volt[start_index:end_index, 0] + y_intercept
        diff = np.max(np.abs(pred - cap_vs_volt[start_index:end_index, 1]))
        if diff > diff_threshold:
            streak_size = end_index - start_index - 1
            break
    streak_dist = np.linalg.norm(cap_vs_volt[start_index, :] - cap_vs_volt[start_index+streak_size, :])
    if slope != 0:
        x_intercept = -1*y_intercept/slope
    else:
        x_intercept = None
    return streak_size, streak_dist, slope, x_intercept, y_intercept


def find_ideal_cv_line(cap_vs_volt, energy_bandgap):
    diff_threshold = .001*np.median(cap_vs_volt[:,1])
    size_threshold = 5
    initial_slope, _, _, _, _ = sp.stats.linregress(cap_vs_volt[:10, :])
    longest_streak_slope, longest_streak_dist, longest_streak_x_intercept, longest_streak_y_intercept = 0,0,0,0
    for start_index in range(cap_vs_volt.shape[0]):
        current_streak_size, current_streak_dist, current_slope, current_x_intercept, current_y_intercept \
            = find_streak(cap_vs_volt, start_index, diff_threshold)
        if (current_slope < min(0, initial_slope)) and \
            (current_x_intercept < energy_bandgap) and \
            (current_streak_dist > longest_streak_dist) and \
            (current_streak_size > size_threshold):

            longest_streak_slope, longest_streak_dist, longest_streak_x_intercept, longest_streak_y_intercept \
                = current_slope,current_streak_dist, current_x_intercept, current_y_intercept

    return longest_streak_slope, longest_streak_x_intercept, longest_streak_y_intercept


def calculate_carrier_density(slope, epsilon_o, epsilon_r, elementary_charge, area, built_in_voltage):
    carrier_density = -2/(elementary_charge*slope*epsilon_o*epsilon_r*area**2*built_in_voltage)
    return carrier_density


def calculate_depletion_width(epsilon_o, epsilon_r, elementary_charge, carrier_density, built_in_voltage):
    depletion_width = np.sqrt((2*epsilon_o*epsilon_r*built_in_voltage)/(elementary_charge*carrier_density))
    return depletion_width


def calculate_energy_intrinsic(energy_conduction, energy_valence, boltzmann, eff_mass_hole, eff_mass_elec, temperature):
    energy_intrinsic = (energy_conduction+energy_valence)/2 + .75*boltzmann*temperature*np.log(eff_mass_hole/eff_mass_elec)
    return energy_intrinsic


def calculate_intrinsic_carrier_concentration(density_of_states_valence, energy_valence, energy_intrinsic,
                                              boltzmann, temperature):
    intrinsic_carrier_concentration = density_of_states_valence*np.exp((energy_valence-energy_intrinsic)/(boltzmann*temperature))
    return intrinsic_carrier_concentration


def calculate_energy_fermi(boltzmann, energy_intrinsic, carrier_density, intrinsic_carrier_concentration, temperature):
    energy_fermi = energy_intrinsic-boltzmann*temperature*np.log(np.abs(carrier_density*(1e-6)/intrinsic_carrier_concentration))

    return energy_fermi


def main():
    config = configparser.RawConfigParser()
    config.read('config.ini')
    directory_name = config['Paths']['data_dir']
    dir = '{0}/Analysis'.format(directory_name)
    if not os.path.isdir(dir):
         os.makedirs(dir)
    csv_name = 'data.csv'
    with open(os.path.join(dir,csv_name), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|',quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Temperature'] + ['Carrier Density'] + ['Depletion Width'] + ['Intrinsic Energy'] +
                        ['Intrinsic Carrier Concentration'] + ['Fermi Energy'])

        for file_number in range(200,205, 5):

            filename = "{0}dev2_T{1}K_F100000HZ_CV.txt".format(directory_name, file_number)
            try:
                cv_raw = np.genfromtxt(filename, delimiter=',', skip_header=1, usecols=(0,1))
            except IOError:
                continue
            capacitances = cv_raw[:,1]
            cap_inverse_square = np.reciprocal(np.square(capacitances))
            cap_vs_volt = np.column_stack((cv_raw[:,0], cap_inverse_square))
            cap_vs_volt_forward = cap_vs_volt[:101, :]
            cap_vs_volt_reverse = cap_vs_volt[101:,:]
            energy_bandgap = config.getfloat('Constants', 'energy_bandgap')

            ideal_forward_slope, ideal_forward_x_intercept, ideal_forward_y_intercept = \
                find_ideal_cv_line(cap_vs_volt_forward, energy_bandgap)

            ideal_reverse_slope, ideal_reverse_x_intercept, ideal_reverse_y_intercept = \
                find_ideal_cv_line(cap_vs_volt_reverse, energy_bandgap)

            print("Ideal Forward Slope = ", ideal_forward_slope)
            print("Ideal Forward X_Intercept = ", ideal_forward_x_intercept)
            print("Ideal Reverse Slope", ideal_reverse_slope)
            print("Ideal Reverse X_intercept", ideal_reverse_x_intercept)

            # *************Creating and Saving Plots****************************
            x_forward = cap_vs_volt_forward[:, 0]
            y_forward = cap_vs_volt_forward[:,1]
            x_reverse = cap_vs_volt_reverse[:, 0]
            y_reverse = cap_vs_volt_reverse[:, 1]
            fig, ax = plt.subplots()
            axes = plt.gca()
            axes.set_ylim([.99*np.min(cap_vs_volt[:,1]), 1.01*np.max(cap_vs_volt[:,1])])
            ax.plot(x_forward, y_forward,'.', markersize = 10, label='Forward Sweep')
            ax.plot(x_reverse, y_reverse, '.', markersize=10, label='Reverse Sweep')
            ax.plot(x_forward, ideal_forward_slope * x_forward + ideal_forward_y_intercept, '-', label='Forward Sweep Ideal Line')
            ax.plot(x_reverse, ideal_reverse_slope * x_reverse + ideal_reverse_y_intercept, '-', label='Reverse Sweep Ideal Line')
            fig.suptitle('Inverse Square Capacitance vs. Voltage-{0}K'.format(file_number), fontsize=20)
            plt.ylabel(r'Inverse Square Capacitance, $C^{-2}(F^{-2})$',fontsize=15)
            plt.xlabel('Voltage, V (Volts)',fontsize=15)
            plt.tick_params(axis='both', which='major', labelsize=15)
            plt.locator_params(axis='y', nbins=5)
            pic_name='CV_{0}K_100kHz.png'.format(file_number)
            # fig.savefig(os.path.join(dir,pic_name))
            plt.show()
            # ******************************************************************

            # ***********************Import Constants From Config*******************************************

            averaged_slope = np.mean((ideal_forward_slope, ideal_reverse_slope))
            averaged_x_intercept = np.mean((ideal_forward_y_intercept, ideal_reverse_y_intercept))
            epsilon_o = config.getfloat('Constants', 'epsilon_o')
            epsilon_r = config.getfloat('Constants', 'epsilon_r')
            elementary_charge = config.getfloat('Constants', 'elementary_charge')
            area = config.getfloat('Constants', 'area')
            energy_conduction = config.getfloat('Constants', 'energy_conduction')
            energy_valence = config.getfloat('Constants', 'energy_valence')
            mass_carrier = config.getfloat('Constants', 'mass_carrier')
            eff_mass_hole = mass_carrier*config.getfloat('Constants', 'relative_hole_eff_mass')
            eff_mass_elec = mass_carrier*config.getfloat('Constants', 'relative_elec_eff_mass')
            boltzmann = config.getfloat('Constants', 'boltzmann')
            volume_nc = (4/3)*np.pi*config.getfloat('Constants', 'radius_nc')**3
            density_of_states_valence = (2/volume_nc)*config.getfloat('Constants', 'packing_fraction')

            # *********************************************************************************************
            carrier_density = calculate_carrier_density(averaged_slope, epsilon_o, epsilon_r,
                                                        elementary_charge,area,built_in_voltage=averaged_x_intercept)

            depletion_width = calculate_depletion_width(epsilon_o, epsilon_r, elementary_charge, carrier_density,
                                                        built_in_voltage=averaged_x_intercept)

            energy_intrinsic = calculate_energy_intrinsic(energy_conduction, energy_valence, boltzmann, eff_mass_hole,
                                                          eff_mass_elec, temperature=file_number)

            intrinsic_carrier_concentration = calculate_intrinsic_carrier_concentration(density_of_states_valence,
                                                                                        energy_valence, energy_intrinsic,
                                                                                        boltzmann, temperature=file_number)

            energy_fermi = calculate_energy_fermi(boltzmann, energy_intrinsic, carrier_density,
                                                  intrinsic_carrier_concentration, temperature=file_number)

            writer.writerow([file_number]+[carrier_density]+[depletion_width]+[energy_intrinsic]+
                            [intrinsic_carrier_concentration]+[energy_fermi])

if __name__ == '__main__':
    main()