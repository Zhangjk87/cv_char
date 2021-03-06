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
    device_num = config['Paths']['device_num']
    dir = '{0}\Analysis'.format(directory_name)
    input_csv_name = 'manual_line_params.csv'
    output_csv_name = 'generated_line_params.csv'
    print("Generating Linear Fit Parameters...")

    data = []

    with open(os.path.join(dir, input_csv_name), 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

        with open(os.path.join(dir, output_csv_name), 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
            writer.writerow(
                ['Temperature'] + ['Frequency'] + ['Ideal Forward Slope'] + ['Ideal Forward Y Intercept'] +
                ['Ideal Forward X Intercept'] + ['Ideal Reverse Slope'] + ['Ideal Reverse Y Intercept'] +
                ['Ideal Reverse X Intercept'])

            for row in reader:

                temp = int(row['Temperature'])
                freq = int(row['Frequency'])
                forward_left_bound = float(row['Forward Left Bound'])
                forward_right_bound = float(row['Forward Right Bound'])
                reverse_left_bound = float(row['Reverse Left Bound'])
                reverse_right_bound = float(row['Reverse Right Bound'])

                filename = "{0}dev{1}_T{2}K_F{3}HZ_CV.txt".format(directory_name, device_num,temp, freq)

                try:
                    cv_raw = np.genfromtxt(filename, delimiter=',', skip_header=1, usecols=(0, 1))
                except IOError:
                    continue

                capacitances = cv_raw[:, 1]
                # voltages = cv_raw[:, 0]
                # voltages_inverse = -1 * voltages
                cap_inverse_square = np.reciprocal(np.square(capacitances))
                cap_vs_volt = np.column_stack((cv_raw[:,0], cap_inverse_square))
                # cap_vs_volt = np.column_stack((voltages_inverse, cap_inverse_square))
                cap_vs_volt_forward = cap_vs_volt[:int(cap_vs_volt.shape[0]/2), :]
                cap_vs_volt_reverse = cap_vs_volt[int(cap_vs_volt.shape[0]/2):, :]
                ideal_forward_x_values = []
                ideal_forward_y_values = []
                ideal_reverse_x_values = []
                ideal_reverse_y_values = []

                for index, voltage in enumerate(cap_vs_volt_forward[:, 0]):
                    if (voltage > forward_left_bound) and (voltage < forward_right_bound):
                        ideal_forward_x_values.append(voltage)
                        ideal_forward_y_values.append(cap_vs_volt_forward[index, 1])

                for index, voltage in enumerate(cap_vs_volt_reverse[:, 0]):
                    if (voltage > reverse_left_bound) and (voltage < reverse_right_bound):
                        ideal_reverse_x_values.append(voltage)
                        ideal_reverse_y_values.append(cap_vs_volt_reverse[index, 1])

                ideal_forward_slope, ideal_forward_y_intercept, _, _, _ = sp.stats.linregress(ideal_forward_x_values,
                                                                                              ideal_forward_y_values)
                ideal_reverse_slope, ideal_reverse_y_intercept, _, _, _ = sp.stats.linregress(ideal_reverse_x_values,
                                                                                              ideal_reverse_y_values)

                ideal_forward_x_intercept = -1*ideal_forward_y_intercept/ideal_forward_slope
                ideal_reverse_x_intercept = -1*ideal_reverse_y_intercept/ideal_reverse_slope

                data.append((freq, temp, ideal_forward_slope, ideal_forward_y_intercept, ideal_forward_x_intercept,
                             ideal_reverse_slope, ideal_reverse_y_intercept, ideal_reverse_x_intercept))

            data_sorted = sorted(data)
            for row in data_sorted:
                writer.writerow(row)

    print("Integrating CSV Files...")
    os.system("csv_replacer.py")
    print("Regenerating Figures...")
    os.system("cv_char_gen_figures.py")



if __name__ == '__main__':
    main()
