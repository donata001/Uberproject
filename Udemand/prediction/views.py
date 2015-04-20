import ast
import csv
from datetime import datetime
from django.views.generic import View

from django.http import HttpResponse
from django.shortcuts import render
import logging
log = logging.getLogger(__name__)

from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ParseError

from .tasks import training_data_processor, test_data_processor,\
map_back_result


DEMAND_TEMPLATE = 'demand.html'


class ProvideStream(APIView):
    
    '''
    sample usage
    curl -i -X POST -H "Content-Type: multipart/form-data" -F "data=@sample.json" http://localhost:8000/uberdemand/upload
    
    sample.json is the file you want to train
    
    '''
    permission_classes = (AllowAny,)

    def post(self, request):
        stream = request.FILES.get('data')
        if not stream:
            raise ParseError('Empty json file.')
        sample = ast.literal_eval(stream.read())
        sample_type = type(sample)
        if sample_type != list:
            raise ParseError('a json stream field required')
            
        training_data_processor(sample)
        return Response({'success': 200})


class GetPrediction(APIView):
    '''
    sample usage
    curl -X GET "http://localhost:8000/uberdemand/predict?start=2015-5-1&end=2015-5-18"
    
    specify the start and end date in YEAR-MM-DD format
    a predicted csv file will be returned
    '''
    permission_classes = (AllowAny,)

    def get(self, request):
        params = request.GET
        start = params.get('start')
        end = params.get('end')

        if not start or not end:
            raise ParseError('start, and end date required')
 
        if start and end:
            st = (int(x) for x in start.split('-'))
            ed = (int(x) for x in end.split('-'))
            try:
                start = datetime(*st)
                end = datetime(*ed)
            except TypeError:
                start = datetime(2012, 5, 1)
                end = datetime(2012, 5, 15)
            result, _ = test_data_processor(start, end)
            if result:
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="prediction.csv"'

                writer = csv.writer(response)
                writer.writerow(['UTC time', 'predicted login count'])
                for line in result:
                    writer.writerow(line)

                return response


    
class PlotResult(View):
    '''
    go to http://localhost:8000/uberdemand/plot to see the predicted result
    move mouse onto the plot to see detailed data.
    '''
    def get(self, request):
        _, result = map_back_result()
        if not result:
            return render(request, DEMAND_TEMPLATE, {'error': 'No result yet to plot, try refresh.'})

        return render(request, DEMAND_TEMPLATE, {'x': result[0],
                                                 'y': result[1]})

