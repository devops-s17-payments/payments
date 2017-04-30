import os

from app import payments
from app.db import app_db
from app.db.interface import PaymentService

def before_all(context):

    ''' 
        this db stuff should go somewhere else
        refactor will be another issue
    '''
    payments.app.debug = True
    payments.app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('LOCAL_DB')
    app_db.drop_all()
    app_db.create_all()
    app_db.session.commit()
    
    context.app = payments.app.test_client()
    context.ps = payments.payment_service

def before_scenario(context, scenario):
    app_db.create_all()
    app_db.session.commit()

def after_scenario(context, scenario):
    app_db.drop_all()
    app_db.session.commit()


def after_all(context):
    app_db.drop_all()
    app_db.session.commit()
