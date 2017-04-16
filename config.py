import os, sys, json

if 'VCAP_SERVICES' in os.environ:
    VCAP_SERVICES = os.environ['VCAP_SERVICES']
    services = json.loads(VCAP_SERVICES)
    creds = services['elephantsql'][0]['credentials']
    name = services['elephantsql'][0]['name']
    if 'test' in name:
        TESTING = True
    SQLALCHEMY_DATABASE_URI = creds['uri']
    print 'Connecting to Bluemix postgres db...'
elif 'LOCAL_DB' in os.environ:
    SQLALCHEMY_DATABASE_URI = os.environ['LOCAL_DB']
    print 'Connecting to local postgres db...'
else:
    print "Missing database config. Exiting..."
    sys.exit(1)

SQLALCHEMY_TRACK_MODIFICATIONS = False
