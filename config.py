import os, sys

'''
for local db, need to EXPORT env variable after vagrant ssh:
export LOCAL_DB = postgresql://payments:payments@localhost:5432/dev
'''

if 'VCAP_SERVICES' in os.environ:
    VCAP_SERVICES = os.environ['VCAP_SERVICES']
    services = json.loads(VCAP_SERVICES)
    creds = services['elephantsql'][0]['credentials']
    SQLALCHEMY_DATABASE_URI = creds['uri']
    print 'Connecting to Bluemix postgres db...'
elif 'LOCAL_DB' in os.environ:
    SQLALCHEMY_DATABASE_URI = os.environ['LOCAL_DB']
    print 'Connecting to local postgres db...'
else:
    print "Missing database config. Exiting..."
    sys.exit(1)

SQLALCHEMY_TRACK_MODIFICATIONS = False