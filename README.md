# Welcome to Payments!

[![Build Status](https://travis-ci.org/devops-s17-payments/payments.svg?branch=master)](https://travis-ci.org/devops-s17-payments/payments)
[![codecov](https://codecov.io/gh/devops-s17-payments/payments/branch/master/graph/badge.svg)](https://codecov.io/gh/devops-s17-payments/payments)


Check us out on Bluemix!

http://nyu-devops-sp17-payments.mybluemix.net/payments"

API Documentation thanks to [Flasgger](https://github.com/rochacbruno/flasgger "Flasgger")

http://nyu-devops-sp17-payments.mybluemix.net/payments"


### How to use this repository ###

First, you need some tools. Download [VirtualBox](https://www.virtualbox.org/ "VirtualBox") and [Vagrant](https://www.vagrantup.com/ "Vagrant")
```
git clone https://github.com/devops-s17-payments/payments
cd payments
vagrant up
vagrant ssh
cd /vagrant
```

### Run some tests! ###

Unit Tests: `nosetests -v --rednose --nologcapture`

Integration Tests: `behave`

### Check out the coverage! ###

`coverage run --omit "/usr/*" -m unittest discover`

`coverage report -m`

### Run the app locally! ###

`python run.py`

Then visit `localhost:5000`

