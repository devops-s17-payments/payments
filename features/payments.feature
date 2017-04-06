Feature: The payments API
	As an e-commerce business owner
	I need a RESTful payments service
	So that my customers can purchase my products


Scenario: The server is running
    When I visit the "home page"
    Then I should see "Welcome to payments"
    Then I should not see "Not Found"