import numpy as np
import matplotlib.pyplot as plt
import sys
import scipy as sp
from scipy import stats
import os
import configparser
import csv


def calculate_carrier_density(slope, epsilon_o, epsilon_r, elementary_charge, area, built_in_voltage):
    carrier_density = -2/(elementary_charge*slope*epsilon_o*epsilon_r*area**2)
    return carrier_density #m^-3


def calculate_depletion_width(epsilon_o, epsilon_r, elementary_charge, carrier_density, built_in_voltage):
    depletion_width = np.sqrt(np.abs((2*epsilon_o*epsilon_r*built_in_voltage))/abs((elementary_charge*carrier_density)))
    return depletion_width #m^-3


def calculate_energy_intrinsic(energy_conduction, energy_valence, boltzmann, eff_mass_hole, eff_mass_elec, temperature):
    energy_intrinsic = (energy_conduction+energy_valence)/2 + .75*boltzmann*temperature*np.log(eff_mass_hole/eff_mass_elec)
    return energy_intrinsic


def calculate_intrinsic_carrier_concentration(density_of_states_valence, energy_valence, energy_intrinsic,
                                              boltzmann, temperature):
    intrinsic_carrier_concentration = density_of_states_valence*np.exp((energy_valence-energy_intrinsic)/(boltzmann*temperature))
    return intrinsic_carrier_concentration #cm^-3


def calculate_energy_fermi(boltzmann, energy_intrinsic, carrier_density, intrinsic_carrier_concentration, temperature):
    energy_fermi = energy_intrinsic-boltzmann*temperature*np.log(np.abs(carrier_density*(1e-6)/intrinsic_carrier_concentration))

    return energy_fermi


def main():
    config = configparser.RawConfigParser()
    config.read('config.ini')
    directory_name = config['Paths']['data_dir']
    device_num = config['Paths']['device_num']
    dir = '{0}\Analysis'.format(directory_name)
    if not os.path.isdir(dir):
         os.makedirs(dir)

    for frequency in range(3, 6):
        freq = 10**frequency

        data = []

        input_csv_name = '{0}_line_params.csv'.format(freq)
        with open(os.path.join(dir, input_csv_name), 'r') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

            output_csv_name = '{0}_data.csv'.format(freq)
            with open(os.path.join(dir, output_csv_name), 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['Temperature'] + ['Carrier Density'] + ['Depletion Width'] + ['Intrinsic Energy'] +
                                ['Intrinsic Carrier Concentration'] + ['Fermi Energy'] + ['Forward Vbi'] + [
                                    'Reverse Vbi'] + ['Averaged Vbi'])

                for row in reader:
                    temp = int(row['Temperature'])
                    ideal_forward_slope = float(row['Ideal Forward Slope'])
                    ideal_forward_y_intercept = float(row['Ideal Forward Y Intercept'])
                    ideal_forward_x_intercept = float(row['Ideal Forward X Intercept'])
                    ideal_reverse_slope = float(row['Ideal Reverse Slope'])
                    ideal_reverse_y_intercept = float(row['Ideal Reverse Y Intercept'])
                    ideal_reverse_x_intercept = float(row['Ideal Reverse X Intercept'])

                    filename = "{0}dev{1}_T{2}K_F{3}HZ_CV.txt".format(directory_name, device_num, temp, freq)
                    try:
                        cv_raw = np.genfromtxt(filename, delimiter=',', skip_header=1, usecols=(0, 1))
                    except IOError:
                        continue

                    capacitances = cv_raw[:, 1]
                    cap_inverse_square = np.reciprocal(np.square(capacitances))
                    # voltages = cv_raw[:, 0]
                    # voltages_inverse = -1 * voltages
                    cap_vs_volt = np.column_stack((cv_raw[:, 0], cap_inverse_square))
                    # cap_vs_volt = np.column_stack((voltages_inverse, cap_inverse_square))
                    cap_vs_volt_forward = cap_vs_volt[:101, :]
                    cap_vs_volt_reverse = cap_vs_volt[101:, :]

                    # *************Creating and Saving Plots********************************************************
                    x_forward = cap_vs_volt_forward[:,0]
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
                    fig.suptitle('Inverse Square Capacitance vs. Voltage-{0}K at {1}Hz'.format(temp, freq), fontsize=20)
                    plt.ylabel(r'Inverse Square Capacitance, $C^{-2}(F^{-2})$',fontsize=15)
                    plt.xlabel('Voltage, V (Volts)',fontsize=15)
                    plt.tick_params(axis='both', which='major', labelsize=15)
                    plt.locator_params(axis='y', nbins=5)
                    pic_name='CV_{0}K_{1}Hz.png'.format(temp, freq)
                    fig.savefig(os.path.join(dir,pic_name))
                    # plt.show()
                    plt.close('all')
                    # **********************************************************************************************

                    # ***********************Import Constants From Config*******************************************

                    averaged_slope = np.mean((ideal_forward_slope, ideal_reverse_slope))
                    averaged_x_intercept = np.mean((ideal_forward_x_intercept, ideal_reverse_x_intercept))
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
                                                                  eff_mass_elec, temp)

                    intrinsic_carrier_concentration = calculate_intrinsic_carrier_concentration(density_of_states_valence,
                                                                                                energy_valence, energy_intrinsic,
                                                                                                boltzmann, temp)

                    energy_fermi = calculate_energy_fermi(boltzmann, energy_intrinsic, carrier_density,
                                                          intrinsic_carrier_concentration, temp)

                    writer.writerow([temp]+[carrier_density]+[depletion_width]+[energy_intrinsic]+
                                    [intrinsic_carrier_concentration]+[energy_fermi]+[ideal_forward_x_intercept]+
                                    [ideal_reverse_x_intercept] + [averaged_x_intercept])

                    data.append((temp, carrier_density, depletion_width, energy_intrinsic,
                                 intrinsic_carrier_concentration, energy_fermi, averaged_x_intercept))

        x_temp, carrier_density, depletion_width, energy_intrinsic, intrinsic_carrier_concentration,\
        energy_fermi, built_in_voltage = zip(*data)

        dependent_vars_list = [carrier_density, depletion_width, energy_intrinsic, intrinsic_carrier_concentration,
                     energy_fermi, built_in_voltage]

        var_names = ['Carrier Density, $cm^{-3}$', 'Depletion Width, $nm$', 'Intrinsic Energy, $eV$',
                     'Intrinsic Carrier Concentration, $cm^{-3}$', 'Fermi Energy, $eV$', 'Vbi, $V$']

        for index, var_name in enumerate(var_names):
            fig, ax = plt.subplots()
            fig.suptitle('Temperature, $K$ vs. {0} at {1}Hz'.format(var_name, freq), fontsize=20)
            plt.ylabel(r'{0}'.format(var_name), fontsize=15)
            plt.xlabel('Temperature, $K$', fontsize=15)
            plt.tick_params(axis='both', which='major', labelsize=15)
            plt.locator_params(axis='y', nbins=5)
            pic_name = 'Temperature vs. {0} at {1}Hz.png'.format(var_name, freq)
            ax.plot(x_temp, dependent_vars_list[index], '.', markersize=10)
            fig.savefig(os.path.join(dir, pic_name))
            # plt.show()
            plt.close('all')


if __name__ == '__main__':
    main()