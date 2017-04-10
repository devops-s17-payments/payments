Feature: The payments API
    As an e-commerce business owner
    I need a RESTful payments service
    So that my customers can purchase my products

Background:
    Given the following payments
        | nickname   | user_id | payment_type | is_default | is_removed | charge_history | user_name    | expires | card_type  | card_number      | user_email | is_linked | 
        | my credit  | 1       | credit       | True       | False      | 0.0            | Jimmy Jones  | 08/2018 | Visa       | 4444333322221111 | None       | None      |
        | my debit   | 2       | debit        | True       | False      | 0.0            | Jenny Joples | 12/2020 | Mastercard | 1111222233334444 | None       | None      |
        | my paypal  | 1       | paypal       | False      | False      | 0.0            | Jimmy Jones  | None    | None       | None             | jj@aol.com | True      |
        | deleted cc | 2       | credit       | False      | True       | 25.0           | Jenny Joples | 08/2018 | Visa       | 4444333322221111 | None       | None      |


Scenario: The server is running
    When I visit the "home page"
    Then I should see "Welcome to payments"
    Then I should not see "Not Found"

Scenario: Add a new payment
    When I visit "/payments"
    Then I should see "my credit"
    Then I should see "my debit"
    Then I should see "my paypal"
    Given a new credit card:
        | nickname   | user_id | payment_type | user_name   | expires | card_type | card_number      |
        | new credit | 1       | credit       | Jimmy Jones | 07/2017 | Visa      | 3333222244441111 |
    When I add a new payment to "/payments"
    And I visit "/payments"
    Then I should see "new credit"
    Then I should see "my credit"
    Then I should see "my debit"
    Then I should see "my paypal"