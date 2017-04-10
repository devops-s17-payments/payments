from app import payments
from app.db import app_db

def before_all(context):

    ''' 
        this db stuff should go somewhere else
        refactor will be another issue
    '''
    payments.app.debug = True
    payments.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://payments:payments@localhost:5432/test'
    app_db.drop_all()    # clean up the last tests
    app_db.create_all()  # make our sqlalchemy tables
    app_db.session.commit()
    
    context.app = payments.app.test_client()
    context.server = payments

def after_all(context):
    app_db.drop_all()