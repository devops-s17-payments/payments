#Welcome to Payments!

**Current payment options supported:**
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
 * PATCH /payments/{id}
 * Accepts JSON in request body. Only need to provide those attributes being changed:

```
{
    "nickname": "my-new-card",
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
* PUT /payments/{id}  (this should be a PATCH, will be updated)

**CHARGE** default payment:
* PUT /payments/charge (this should be a PATCH, will be updated)
* Accepts JSON in request body in the following format:

```
{
    'amount' : 19.99
}
```
