import dateutil.parser
import calendar
import os
from datetime import datetime, timedelta
from subprocess import call, check_output
from collections import defaultdict
import ast
import csv
import logging
log = logging.getLogger(__name__)


PWD = os.path.dirname(__file__) + '/datamodel'

PATH = PWD
MODEL_PATH = PWD + '/model'
INPUT = PWD + '/data.csv'
TEMP = PWD + '/temp.arff'
TEST_RESULT_FILE = PWD + '/test_result'
RAW_TEST = PWD + "/test.csv"
DEMAND_TEMPLATE = 'demand.html'
DEFAULT_DATA = PWD + '/sample.json'


def read_data():
    with open(DEFAULT_DATA) as f:
        lines = f.readlines()[0]
        data_list = ast.literal_eval(lines)
    return data_list


def train():
    '''
    training with weka's KNN classifier, tested classifiers include ANN, SVR, KNN,
    spesifically KNN with K=1 provided the overall best performance. 10 fold cross-validation
    Root mean squared error was used as a key matrix to judge the performance. After each 
    training cycle, a new model is dumped.
    '''

    BASE_CLASSFIER = 'weka.classifiers.lazy.IBk'
    if not os.path.isfile(INPUT):
        raise IOError('No training file.')

    cmd = 'java -cp weka.jar %s -t %s -x 10 > result 2>error' % \
         (BASE_CLASSFIER, INPUT)
    call(cmd, cwd=PATH, shell=True)
    error = check_output("grep mean result | tail -1 |awk '{print $5}'",
                          cwd=PATH, shell=True)
    log.info('training new model with Root mean squared error %s', error)
    call('java -cp weka.jar %s -t %s -d %s' % (BASE_CLASSFIER, INPUT,
                                               MODEL_PATH),
                                               cwd=PATH, shell=True)


def preprocess(FILE_PATH, train=True):
    log.info('prepare file...')
    if train:
        OUTPUT = 'datamodel/train_filtered_data.arff'
    else:
        OUTPUT = 'datamodel/test_filtered_data.arff'
    CSV_LOADER = 'weka.core.converters.CSVLoader'
    NumericToNominal = 'weka.filters.unsupervised.attribute.NumericToNominal -R first-3'

    Tocsv = 'java -cp weka.jar %s %s > %s' % (CSV_LOADER, FILE_PATH,
                                                   TEMP)
    ToNominal = 'java -cp weka.jar %s -i %s -o %s' % (NumericToNominal, TEMP,
                                                   OUTPUT)
    call(Tocsv + ';' + ToNominal, cwd=PATH, shell=True)
    return OUTPUT


# @param datetime object, datetime object
def generate_test_file(start, end):
    
    '''
    generating an unlabeled test file with same attribute as training file, x-axis is
    hourly based.
    
    
    Here is the generated test file sample:
    
    day,hour,weekday,timestamp,count
    1,0,4,1430438400,?
    1,1,4,1430442000,?
    1,2,4,1430445600,?
    1,3,4,1430449200,?
    1,4,4,1430452800,?
    1,5,4,1430456400,?
    1,6,4,1430460000,?
    1,7,4,1430463600,?
    1,8,4,1430467200,?

    '''
    log.info('generate test file')
    csv_file = open(RAW_TEST, 'wb')
    writer = csv.writer(csv_file, dialect='excel', quoting=csv.QUOTE_MINIMAL,
                        lineterminator='\n')

    writer.writerow(['day', 'hour', 'weekday', 'timestamp', 'count'])

    dt = start
    while dt <= end:
        timestamp = calendar.timegm(dt.timetuple())
        writer.writerow([dt.day, dt.hour, dt.weekday(), timestamp, '?'])
        dt += timedelta(hours=1)
    csv_file.close()
    log.info('new test file generated.')


def predict():
    ''' predict test file with dumped model, ? is the class attribute to be predicted
    
    Here is the sample for a predicted test file
    === Predictions on test data ===

     inst#     actual  predicted      error (day,hour,weekday,timestamp)
         1          ?     21              ? (1,0,1,1335830400)
         2          ?     18              ? (1,1,1,1335834000)
         3          ?     14              ? (1,2,1,1335837600)
         4          ?      6              ? (1,3,1,1335841200)
         5          ?      6              ? (1,4,1,1335844800)
         6          ?      3              ? (1,5,1,1335848400)
         7          ?      2              ? (1,6,1,1335852000)
         8          ?      2              ? (1,7,1,1335855600)
         9          ?      4              ? (1,8,1,1335859200)
        10          ?      7              ? (1,9,1,1335862800)
    
    '''

    BASE_CLASSFIER = 'weka.classifiers.lazy.IBk'

    log.info('predict new test set...')
    if not os.path.isfile(RAW_TEST):
        raise IOError('No test file.')
    call('java -cp weka.jar %s -l %s -T %s -p 1-5> test_result 2>error' % (BASE_CLASSFIER, MODEL_PATH,
                                                   RAW_TEST),
                                                   cwd=PATH, shell=True)
    #print call('cat test_result', cwd=PATH, shell=True)


def mock():
    d1 = datetime(2012, 5, 1, 0, 0, 0)
    d2 = datetime(2012, 5, 15, 0, 0, 0)
    generate_test_file(d1, d2)
    train()
    predict()


def map_back_result():
    
    if not os.path.isfile(TEST_RESULT_FILE):
        raise IOError('No test file for mapping.')
    f = open(TEST_RESULT_FILE)
    lines = f.readlines()[5:-1]
    f.close()
    result = []
    plot_list = [[], []]

    for line in lines:
        splited = line.split()
        predicted = splited[2]
        timestamp = ast.literal_eval(splited[-1])[-1]
        dt = datetime.utcfromtimestamp(timestamp)
        utc = dt.isoformat()
        result.append([utc, int(predicted)])
        plot_list[0].append(utc)
        plot_list[1].append(int(predicted))
    return result, plot_list


def training_data_processor(login_list):
    '''
    processing stream data, get hourly count and generate a training file,
    the key part is feature selection, (assume data range does not cover special
    season), day, hour, weekday can all be treated as norminal attribute but timestamp
    is the proceeding time which makes the problem a time-series prediction, the
    first three attributes can be easily transformed to a linear part.
    
    '''
    counter = defaultdict(int)
    for login in login_list:
        dt = dateutil.parser.parse(login)
        year = dt.year
        month = dt.month
        day = dt.day
        hour = dt.hour
        counter[year, month, day, hour] += 1

    pending = sorted(counter.keys())
    csv_file = open(INPUT, 'wb')
    writer = csv.writer(csv_file, dialect='excel', quoting=csv.QUOTE_MINIMAL,
                        lineterminator='\n')

    writer.writerow(['day', 'hour', 'weekday', 'timestamp', 'count'])
    for k in pending:
        dt = datetime(*k)
        weekday = dt.weekday()
        timestamp = calendar.timegm(dt.timetuple())
        writer.writerow(list(k[2:]) + [weekday, timestamp, counter[k]])

    csv_file.close()
    train()


def test_data_processor(start, end):
    generate_test_file(start, end)
    predict()
    result = map_back_result()
    return result