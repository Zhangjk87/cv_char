import numpy as np
import matplotlib.pyplot as plt
import sys
import scipy as sp
from scipy import stats
import os
import configparser
import csv


def main():
    config = configparser.RawConfigParser()
    config.read('config.ini')
    directory_name = config['Paths']['data_dir']
    dir = '{0}/Analysis'.format(directory_name)

    for frequency in range(3, 6):
        freq = 10 ** frequency

        data = []

        input_csv_name = '{0}_data.csv'.format(freq)

        with open(os.path.join(dir, input_csv_name), 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            next(reader, None)
            for row in reader:
                data.append(row)

        x_temp, carrier_density, depletion_width, energy_intrinsic, intrinsic_carrier_concentration, \
            energy_fermi, _, _, built_in_voltage = zip(*data)

        output_csv_name = '{0}_averaged_data.csv'.format(freq)
        with open(os.path.join(dir, output_csv_name), 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['Variable']+ ['Average Value'] + ['Uncertainty'])

            temp_left_bound = config['Temp Bounds']['lower_bound']
            temp_right_bound = config['Temp Bounds']['upper_bound']

            temperatures = []
            carrier_densities = []
            depletion_widths = []
            built_in_voltages = []

            list_vars_names = ['Carrier Density', 'Depletion Width', 'Built in Voltage']
            list_vars = [carrier_densities, depletion_widths, built_in_voltages]

            for index, temp in enumerate(x_temp):
                if (temp > temp_left_bound) and (temp < temp_right_bound):
                    temperatures.append(float(temp))
                    carrier_densities.append(float(carrier_density[index]))
                    depletion_widths.append(float(depletion_width[index]))
                    built_in_voltages.append(float(built_in_voltage[index]))

            for index, data_var in enumerate(list_vars):
                _, _, _, _, stderr = sp.stats.linregress(temperatures, data_var)
                np.mean(data_var)
                writer.writerow([list_vars_names[index]] + [np.mean(data_var)] + [stderr])


if __name__ == '__main__':
    main()
