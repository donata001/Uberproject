# UberDemand Prediction
  
**Author**: Jialin Yu
**Date**: Apr.20, 2015

##System requirement:

brew install python

pip install Django

pip install djangorestframework

pip install python-dateutil

git clone git@github.com:donata001/Uberproject.git

goto /Uberproject/Udemand and run python manage.py runserver

and you are good to run the app!


### 1, sample usage to upload your json file for training through a POST request:

    curl -i -X POST -H "Content-Type: multipart/form-data" -F "data=@sample.json" http://localhost:8000/uberdemand/upload
    
    sample.json is the file you want to train

### 2, sample usage to get a prediction from a GET request

    curl -X GET "http://localhost:8000/uberdemand/predict?start=2015-5-1&end=2015-5-18"
    
    specify the start and end date in YEAR-MM-DD format
    a predicted csv file will be returned

### 3, go to http://localhost:8000/uberdemand/plot to see the predicted result
    move mouse onto the plot to see detailed data.
