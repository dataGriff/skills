Feature: Gift card redemption
  As a shopper with a gift card
  I want to pay for orders with the card
  so that I spend its balance before it expires.

  Rule: A redemption must not exceed the card balance

    Scenario: Redemption within the balance
      Given a gift card with a balance of 50
      When the shopper redeems 30
      Then 30 is deducted from the card
      And the card balance is 20

    Scenario: Redemption exceeding the balance is refused
      Given a gift card with a balance of 50
      When the shopper attempts to redeem 80
      Then the redemption is refused because of "insufficient balance"
      And the card balance is 50

  Rule: Expired cards cannot be redeemed

    Scenario: Redemption from an expired card is refused
      Given an expired gift card with a balance of 50
      When the shopper attempts to redeem 10
      Then the redemption is refused because of "card expired"
      And the card balance is 50

  Rule: Any amount up to the full balance can be redeemed

    Scenario Outline: Redemption reduces the balance
      Given a gift card with a balance of <initial>
      When the shopper redeems <amount>
      Then <amount> is deducted from the card
      And the card balance is <remaining>

      Examples:
        | initial | amount | remaining |
        | 100     | 40     | 60        |
        | 25      | 25     | 0         |
