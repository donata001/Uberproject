from django.conf.urls import patterns, url

from  prediction.views import GetPrediction, PlotResult, ProvideStream


urlpatterns = patterns(
    '',
    url(r'^uberdemand/predict$', GetPrediction.as_view()),
    url(r'^uberdemand/plot$', PlotResult.as_view()),
    url(r'^uberdemand/upload$', ProvideStream.as_view()),

)