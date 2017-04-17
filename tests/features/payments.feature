Feature: The payments API
    As an e-commerce business owner
    I need a RESTful payments service
    So that my customers can purchase my products

Background:
    Given the following "payments"
        | nickname   | user_id | payment_type | user_name    | expires | card_type  | card_number      | user_email | is_linked | 
        | my credit  | 1       | credit       | Jimmy Jones  | 08/2018 | Visa       | 4444333322221111 | None       | None      |
        | my debit   | 2       | debit        | Jenny Joples | 12/2020 | Mastercard | 1111222233334444 | None       | None      |
        | my paypal  | 1       | paypal       | Jimmy Jones  | None    | None       | None             | jj@aol.com | True      |

Scenario: The server is running
    When I visit the "home page"
    Then I should see "Welcome to payments" with status code "200"
    Then I should not see "Not Found"

Scenario: Add a new payment
    When I visit "payments"
    Then I should see "3" existing payments
    Given a new credit card
        | nickname   | user_id | payment_type | user_name   | expires | card_type | card_number      |
        | new credit | 1       | credit       | Jimmy Jones | 07/2017 | Visa      | 3333222244441111 |
    When I add a new payment to "payments"
    And I visit "payments"
    Then I should see "4" existing payments
    And I should see "new credit"

Scenario: Update a payment (PATCH)
    When I get "payments" with id "1"
    Then I should see a payment with id "1" and "nickname" = "my credit"
    When I change "nickname" to "new credit"
    And I patch "payments" with id "1"
    When I get "payments" with id "1"
    Then I should see a payment with id "1" and "nickname" = "new credit"

Scenario: Update a payment (PUT)
    When I get "payments" with id "1"
    Then I should see a payment with id "1" and "nickname" = "my credit"
    Given an updated credit card
        | nickname  | user_id | payment_type | user_name   | expires | card_type | card_number      |
        | cashmoney | 1       | credit       | Jimmy Jones | 08/2018 | Visa      | 4444333322221111 |
    When I put "payments" with id "1"
    And I get "payments" with id "1"
    Then I should see a payment with id "1" and "nickname" = "cashmoney"
    When I visit "payments"
    Then I should not see "my credit"

Scenario: Update a payment with bad or no data (PATCH)
    When I get "payments" with id "1"
    Then I should see a payment with id "1" and "nickname" = "my credit"
    When I change "nicknam3" to "new credit", but misspell the attribute
    And I patch "payments" with id "1"
    Then I should see "body of request contains invalid/un-updatable fields"
    When I patch "payments" with id "1" with no data
    Then I should see "body of request contained bad or no data" with status code "400"

Scenario: Update a payment with illegal data (PUT)
    When I get "payments" with id "1"
    Then I should see a payment with id "1" and "nickname" = "my credit"
    Given an updated credit card with illegal data
        | nickname  | user_id | payment_type | user_name   | expires | card_type | card_number      | is_removed |
        | cashmoney | 1       | credit       | Jimmy Jones | 08/2018 | Visa      | 4444333322221111 | True       |
    When I put "payments" with id "1"
    Then I should see "You cannot modify the field: is_removed" with status code "400"

Scenario: Set default payment
    When user with id "1" has existing "payments"
    And user with id "1" performs "set-default" on "payments" with id "1"
    When I get "payments" with id "1"
    Then user with id "1" should see payment with id "1" set as default

Scenario: Delete an existing payment
    When I try to delete payment 1
    Then I should be returned nothing for payment 1
    When I attempt to retrieve the deleted payment 1
    Then the server should tell me payment 1 was not found
    When I try to delete a non-existent payment with id 100
    Then I should be returned nothing for payment 100
