import numpy as np
import matplotlib.pyplot as ml
import sys
import scipy as sp

def find_streak(cap_vs_volt, start_index, rsq_threshold):
    slope, intercept, r_value = 0,0,0
    for end_index in range(start_index+3, len(cap_vs_volt)):
        slope, intercept, r_value, = sp.stats.linregress(cap_vs_volt[start_index:end_index])
        if r_value**2 < rsq_threshold:
            break
    streak_size = end_index-start_index-1
    return streak_size, slope, intercept


def find_idealCV_line(cap_vs_volt):
    find_streak(cap_vs_volt, start_index, rsq_treshold)
    pass


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


        # fig = ml.figure()
        # ax = fig.add_subplot(1, 1, 1)
        # x = cap_vs_volt_forward[:,0]
        # y = cap_vs_volt_forward[:,1]
        # ax.scatter(x, y)
        # ml.show()




if __name__ == '__main__':
    main(sys.argv[1:])