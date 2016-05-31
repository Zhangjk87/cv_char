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
    input_csv_name = 'manual_line_params.csv'
    output_csv_name = 'generated_line_params.csv'

    temperature = []
    frequency = []
    forward_left_bound = []
    forward_right_bound = []
    reverse_left_bound = []
    reverse_right_bound = []

    with open(os.path.join(dir, input_csv_name), 'r') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in reader:
            temperature.append(int(row['Temperature']))
            frequency.append(int(row['Frequency']))
            forward_left_bound.append(float(row['Forward Left Bound']))
            forward_right_bound.append(float(row['Forward Right Bound']))
            reverse_left_bound.append(float(row['Reverse Left Bound']))
            reverse_right_bound.append(float(row['Reverse Right Bound']))

    with open(os.path.join(dir, output_csv_name), 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Temperature'] + ['Frequency'] + ['Ideal Forward Slope'] + ['Ideal Forward Y Intercept'] +
                        ['Ideal Forward X Intercept'] + ['Ideal Reverse Slope'] + ['Ideal Reverse Y Intercept'] +
                        ['Ideal Reverse X Intercept'])

        for file_num in range(len(temperature)):
            temp = temperature[file_num]
            freq = frequency[file_num]
            filename = "{0}dev3_T{1}K_F{2}HZ_CV.txt".format(directory_name, temp, freq)

            try:
                cv_raw = np.genfromtxt(filename, delimiter=',', skip_header=1, usecols=(0, 1))
            except IOError:
                continue

            capacitances = cv_raw[:, 1]
            cap_inverse_square = np.reciprocal(np.square(capacitances))
            cap_vs_volt = np.column_stack((cv_raw[:, 0], cap_inverse_square))
            cap_vs_volt_forward = cap_vs_volt[:101, :]
            cap_vs_volt_reverse = cap_vs_volt[101:, :]
            ideal_forward_x_values = []
            ideal_forward_y_values = []
            ideal_reverse_x_values = []
            ideal_reverse_y_values = []

            for index, voltage in enumerate(cap_vs_volt_forward[:, 0]):
                if (voltage > forward_left_bound[file_num]) and (voltage < forward_right_bound[file_num]):
                    ideal_forward_x_values.append(voltage)
                    ideal_forward_y_values.append(cap_vs_volt_forward[index, 1])

            for index, voltage in enumerate(cap_vs_volt_reverse[:, 0]):
                if (voltage > reverse_left_bound[file_num]) and (voltage < reverse_right_bound[file_num]):
                    ideal_reverse_x_values.append(voltage)
                    ideal_reverse_y_values.append(cap_vs_volt_reverse[index, 1])

            ideal_forward_slope, ideal_forward_y_intercept, _, _, _ = sp.stats.linregress(ideal_forward_x_values,
                                                                                          ideal_forward_y_values)
            ideal_reverse_slope, ideal_reverse_y_intercept, _, _, _ = sp.stats.linregress(ideal_reverse_x_values,
                                                                                          ideal_reverse_y_values)

            ideal_forward_x_intercept = -1*ideal_forward_y_intercept/ideal_forward_slope
            ideal_reverse_x_intercept = -1*ideal_reverse_y_intercept/ideal_reverse_slope

            writer.writerow([temp]+[freq]+[ideal_forward_slope]+[ideal_forward_y_intercept]+
                            [ideal_forward_x_intercept]+[ideal_reverse_slope]+[ideal_reverse_y_intercept]+
                            [ideal_reverse_x_intercept])

if __name__ == '__main__':
    main()
