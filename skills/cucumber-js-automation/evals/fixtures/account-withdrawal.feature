Feature: Account withdrawal
  As an account holder, I want to withdraw cash
  so that I can pay where cards are not accepted.

  Background:
    Given Alice has an open account with a balance of £100

  Rule: Withdrawals must not exceed the available balance

    Scenario: Withdrawal within the balance
      When Alice withdraws £80
      Then £80 is dispensed
      And Alice's balance is £20

    Scenario: Withdrawal exceeding the balance
      When Alice attempts to withdraw £120
      Then nothing is dispensed
      And Alice is told the withdrawal exceeds her balance
      And Alice's balance is £100

    Scenario Outline: Balance after a withdrawal
      When Alice withdraws £<amount>
      Then Alice's balance is £<remaining>

      Examples:
        | amount | remaining |
        | 20     | 80        |
        | 100    | 0         |
