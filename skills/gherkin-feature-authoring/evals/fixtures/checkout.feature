Feature: Checkout

  Scenario: Test 1
    Given the database is cleared
    And I open "https://shop.example.com/login"
    When I type "test@test.com" into the "email" field and type "Passw0rd!" into the "password" field and click the "Log in" button
    Then I see the text "My account"
    When I click "Add to basket" on the first product
    Then the basket count is "1"
    When I click the "Checkout" button
    And I click the "Pay now" button
    Then I see the text "Order confirmed"

  Scenario: Test 2
    When I click "Orders" in the navigation bar
    Then I see the order from Test 1 at the top of the list

  Scenario: Test 3
    Given I am on the checkout page
    When I click the "Pay now" button without entering a delivery address
