## Welcome to Payments!

[![Build Status](https://travis-ci.org/devops-s17-payments/payments.svg?branch=master)](https://travis-ci.org/devops-s17-payments/payments)
[![codecov](https://codecov.io/gh/devops-s17-payments/payments/branch/master/graph/badge.svg)](https://codecov.io/gh/devops-s17-payments/payments)

**Current payment options include:**
* Credit Card
* Debit Card
* Paypal

**Payment Method**
```
{
    "charge-history": 0.0,
    "default": false,
    "detail": {
        "expires": "08/2018",
        "name": "Jane Jenkins",
        "number": "9876543212345678",
        "type": "Visa"
    },
    "id": 2,
    "nickname": "my-debit",
    "type": "debit"

}
```

**How to use this API**

**CREATE** a payment method:
 * POST /payments
 * Accepts JSON in request body in following format:
 
```
 {
    "detail":
    {
        "expires": "08/2018",
        "name": "Jane Jenkins",
        "number": "9876543212345678",
        "type": "Visa"
    },
    "nickname": "my-debit",
    "type": "debit"
}
```

**RETRIEVE** a payment method:
 * GET /payments/{id}

**UPDATE** a payment method:
 * PUT /payments/{id}
 * Accepts JSON in request body. Need to provide entire object as with CREATE.

```
 {
    "detail":
    {
        "expires": "08/2018",
        "name": "Jane Jenkins",
        "number": "9876543212345678",
        "type": "Visa"
    },
    "nickname": "my-new-debit",
    "type": "debit"
}
```

**UPDATE** a payment method:
 * PATCH /payments/{id}
 * Accepts JSON in request body. Only need to provide those attributes being changed:

```
{
    "nickname": "updated-debit",
}
```

**DELETE** a payment method:
 * DELETE /payments/{id}

**LIST** all payment methods:
* GET /payments

**QUERY** payments:
* GET /payments?{key}={value}
* Example: To return all credit card payment methods: /payments?type=credit

**SET** default payment:
* PUT /payments/{id}/set-default  (this should be a PATCH, will be updated)

**CHARGE** default payment:
* PUT /payments/charge (this should be a PATCH, will be updated)
* Accepts JSON in request body in the following format:

```
{
    "amount" : 19.99
}
```
