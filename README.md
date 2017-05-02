# Welcome to Payments!

[![Build Status](https://travis-ci.org/devops-s17-payments/payments.svg?branch=master)](https://travis-ci.org/devops-s17-payments/payments)
[![codecov](https://codecov.io/gh/devops-s17-payments/payments/branch/master/graph/badge.svg)](https://codecov.io/gh/devops-s17-payments/payments)


Check us out on Bluemix: http://nyu-devops-sp17-payments.mybluemix.net

and here's the containerized version: https://nyu-devops-sp17-payments-docker.mybluemix.net/

API Documentation thanks to [Flasgger](https://github.com/rochacbruno/flasgger "Flasgger")

http://nyu-devops-sp17-payments.mybluemix.net/apidocs/index.html


### How to use this repository ###

First, you need some tools. Download [VirtualBox](https://www.virtualbox.org/ "VirtualBox") and [Vagrant](https://www.vagrantup.com/ "Vagrant")

Next, export these environment variables *on your machine* so the Docker Container can use them to create the database:

```
export DB_USER=payments
export DB_PASSWORD=payments
export DB_NAME=dev
export LOCAL_DB=postgresql://payments:payments@localhost:5432/dev
```

Now let's get started:

```
git clone https://github.com/devops-s17-payments/payments
cd payments
vagrant up
vagrant ssh
cd /vagrant
```

### And we're running ###

The database and application containers are now running. Check them out with `docker ps`

You can access the app at `localhost:5000`


### Run some tests! ###

Unit Tests: `nosetests -v --rednose --nologcapture`

Integration Tests: `behave`

### Check out the coverage! ###

`coverage run --omit "/usr/*" -m unittest discover`

`coverage report -m`

