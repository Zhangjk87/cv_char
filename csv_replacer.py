import os
import configparser
import csv

def main():
    config = configparser.RawConfigParser()
    config.read('config.ini')
    directory_name = config['Paths']['data_dir']
    dir = '{0}/Analysis'.format(directory_name)
    if not os.path.isdir(dir):
         os.makedirs(dir)

    input_csv_name = 'generated_line_params.csv'
    csv_name_1000 = '1000_line_params.csv'
    csv_name_10000 = '10000_line_params.csv'
    csv_name_100000 = '100000_line_params.csv'

    data_dict = {'1000': None, '10000': None, '100000': None}

    with open(os.path.join(dir, input_csv_name), 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        next(reader, None)
        generated_line_params = [tuple(line) for line in csv.reader(csvfile)]

    for freq_factor in range(3, 6):
        frequency = 10 ** freq_factor

        with open(os.path.join(dir, '{0}_line_params.csv'.format(frequency)), 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            next(reader, None)
            data_dict['{0}'.format(frequency)] = [tuple(line) for line in csv.reader(csvfile)]

    for data_tuple in generated_line_params:
        freq = data_tuple[0]
        temperature = data_tuple[1]
        i = [temp[0] for temp in data_dict[freq]].index(temperature)
        data_dict[freq][i] = data_tuple[1:]

    for freq_factor in range(3, 6):
        frequency = 10 ** freq_factor

        with open(os.path.join(dir, '{0}_line_params.csv'.format(frequency)), 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(
                ['Temperature'] + ['Ideal Forward Slope'] + ['Ideal Forward Y Intercept'] +
                ['Ideal Forward X Intercept'] + ['Ideal Reverse Slope'] + ['Ideal Reverse Y Intercept'] +
                ['Ideal Reverse X Intercept'])
            for row in data_dict['{0}'.format(frequency)]:
                writer.writerow(row)

if __name__ == '__main__':
    main()