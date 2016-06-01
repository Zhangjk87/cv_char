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


def find_ideal_cv_line(cap_vs_volt, energy_bandgap, diff_threshold_fraction):
    diff_threshold = diff_threshold_fraction*np.median(cap_vs_volt[:,1])
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


def main():
    config = configparser.RawConfigParser()
    config.read('config.ini')
    directory_name = config['Paths']['data_dir']
    dir = '{0}/Analysis'.format(directory_name)
    if not os.path.isdir(dir):
        os.makedirs(dir)

    for frequency in range(3, 6):
        freq = 10 ** frequency

        csv_name = '{0}_line_params.csv'.format(freq)
        with open(os.path.join(dir, csv_name), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                ['Temperature'] + ['Ideal Forward Slope'] + ['Ideal Forward Y Intercept'] +
                ['Ideal Forward X Intercept'] + ['Ideal Reverse Slope'] + ['Ideal Reverse Y Intercept'] +
                ['Ideal Reverse X Intercept'])

            for file_number in range(200, 335, 5):

                print('Currently Working on Data of Temperature: {0} at Frequency {1}'.format(file_number, freq))
                filename = "{0}dev3_T{1}K_F{2}HZ_CV.txt".format(directory_name, file_number, freq)
                try:
                    cv_raw = np.genfromtxt(filename, delimiter=',', skip_header=1, usecols=(0, 1))
                except IOError:
                    continue
                capacitances = cv_raw[:, 1]
                cap_inverse_square = np.reciprocal(np.square(capacitances))
                cap_vs_volt = np.column_stack((cv_raw[:, 0], cap_inverse_square))
                cap_vs_volt_forward = cap_vs_volt[:101, :]
                cap_vs_volt_reverse = cap_vs_volt[101:, :]
                energy_bandgap = config.getfloat('Constants', 'energy_bandgap')

                diff_threshold_fraction = .0015
                ideal_forward_slope, ideal_forward_x_intercept, ideal_forward_y_intercept = \
                    find_ideal_cv_line(cap_vs_volt_forward, energy_bandgap, diff_threshold_fraction)

                ideal_reverse_slope, ideal_reverse_x_intercept, ideal_reverse_y_intercept = \
                    find_ideal_cv_line(cap_vs_volt_reverse, energy_bandgap, diff_threshold_fraction)

                if ideal_forward_slope is 0 or ideal_reverse_slope is 0:
                    diff_threshold_fraction = .015
                    ideal_forward_slope, ideal_forward_x_intercept, ideal_forward_y_intercept = \
                        find_ideal_cv_line(cap_vs_volt_forward, energy_bandgap, diff_threshold_fraction)

                    ideal_reverse_slope, ideal_reverse_x_intercept, ideal_reverse_y_intercept = \
                        find_ideal_cv_line(cap_vs_volt_reverse, energy_bandgap, diff_threshold_fraction)

                writer.writerow([file_number]+[ideal_forward_slope]+[ideal_forward_y_intercept]+[ideal_forward_x_intercept]
                                +[ideal_reverse_slope]+[ideal_reverse_y_intercept]+[ideal_reverse_x_intercept])

            csv_name = 'manual_line_params.csv'
            with open(os.path.join(dir, csv_name), 'w') as csvfile:
                writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['Temperature']+['Frequency']+['Forward Left Bound']+['Forward Right Bound']+
                                ['Reverse Left Bound']+['Reverse Right Bound'])

if __name__ == '__main__':
    main()
