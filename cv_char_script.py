import numpy as np
import matplotlib.pyplot as plt
import sys
import scipy as sp
from scipy import stats


def find_streak(cap_vs_volt, start_index, p_threshold):
    slope, intercept, p_value, streak_size = 0,0,0,0
    for end_index in range(start_index+3, cap_vs_volt.shape[0]):
        slope, intercept, _, p_value, _ = sp.stats.linregress(cap_vs_volt[start_index:end_index, :])
        if p_value > p_threshold:
            streak_size = end_index - start_index - 1
            break
    streak_dist = np.linalg.norm(cap_vs_volt[start_index, :] - cap_vs_volt[start_index+streak_size, :])
    if slope != 0:
        x_intercept = -1*intercept/slope
    else:
        x_intercept = None
    return streak_size, streak_dist, slope, x_intercept

# def find_idealCV_line_generator(cap_vs_volt):
#     energy_bandgap = 1.5
#     p_threshold = .01
#     size_threshold = 5
#     initial_slope, _, _, _, _ = sp.stats.linregress(cap_vs_volt[:10, :])
#     longest_streak_slope, longest_streak_dist, longest_streak_x_intercept = 0,0,0
#     for start_index in range(cap_vs_volt.shape[0]):
#         yield find_streak(cap_vs_volt, start_index, p_threshold)


def find_idealCV_line(cap_vs_volt):
    energy_bandgap = 1.5
    p_threshold = .01
    size_threshold = 0
    initial_slope, _, _, _, _ = sp.stats.linregress(cap_vs_volt[:10, :])
    longest_streak_slope, longest_streak_dist, longest_streak_x_intercept = 0,0,0
    for start_index in range(cap_vs_volt.shape[0]):
        current_streak_size, current_streak_dist, current_slope, current_x_intercept = find_streak(cap_vs_volt, start_index, p_threshold)
        # maybe threshold for how much more negative the slope should be
        if (current_slope < min(0, initial_slope)) and \
            (current_x_intercept < energy_bandgap) and \
            (current_streak_dist > longest_streak_dist) and \
            (current_streak_size > size_threshold):

            longest_streak_slope, longest_streak_dist, longest_streak_x_intercept = current_slope,\
                                                                                    current_streak_dist,\
                                                                                    current_x_intercept

    return longest_streak_slope, longest_streak_x_intercept



def main(argv):
    directoryname = argv[0]

    for file_number in range(200, 205, 5):
        filename = "{0}dev2_T{1}K_F100000HZ_CV.txt".format(directoryname, file_number)
        try:
            cv_raw = np.genfromtxt(filename, delimiter=',', skip_header=1, usecols=(0,1))
        except IOError:
            continue
        capacitances = cv_raw[:,1]
        cap_inverse_square = np.reciprocal(np.square(capacitances))
        cap_vs_volt = np.column_stack((cv_raw[:,0], cap_inverse_square))
        print(cap_vs_volt)
        cap_vs_volt_forward = cap_vs_volt[:101, :]
        cap_vs_volt_reverse = cap_vs_volt[101:,:]
        x = cap_vs_volt_forward[:, 0]
        y = cap_vs_volt_forward[:,1]
        fig, ax = plt.subplots()
        ax.plot(x, y,'.', markersize = 2,)
        ideal_slope, ideal_x_intercept = find_idealCV_line(cap_vs_volt_forward)
        # ax.plot(x, ideal_slope * x + ideal_x_intercept * (-ideal_slope), '-')
        print("Slope = ", ideal_slope)
        print("X_Intercept = ", ideal_x_intercept)
        plt.show()


# def main(argv):
    # directoryname = argv[0]

    # for file_number in range(200, 205, 5):
    #     filename = "{0}dev2_T{1}K_F100000HZ_CV.txt".format(directoryname, file_number)
    #     try:
    #         cv_raw = np.genfromtxt(filename, delimiter=',', skip_header=1, usecols=(0,1))
    #     except IOError:
    #         continue
    #     capacitances = cv_raw[:,1]
    #     cap_inverse_square = np.reciprocal(np.square(capacitances))
    #     cap_vs_volt = np.column_stack((cv_raw[:,0], cap_inverse_square))
    #     print(cap_vs_volt)
    #     cap_vs_volt_forward = cap_vs_volt[:101, :]
    #     cap_vs_volt_reverse = cap_vs_volt[101:,:]
    #     x = cap_vs_volt_forward[:, 0]
    #     y = cap_vs_volt_forward[:,1]
    #     fig, ax = plt.subplots()
    #     ax.plot(x, y,'.', markersize = 25,)
    #     for size, dist, slope, x_intercept in find_idealCV_line_generator(cap_vs_volt_forward):
    #         if x_intercept is None or slope > 0:
    #             continue
    #         ax.plot(x, slope * x + x_intercept * (-slope), '-')
    #     plt.show()



if __name__ == '__main__':
    main(sys.argv[1:])