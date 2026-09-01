@billing
Feature: Account withdrawal
  As an account holder, I want to withdraw cash from my account
  so that I can pay where cards are not accepted.

  Scope: cash withdrawals at ATMs and branch counters. Transfers and
  card payments are covered in their own features.

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
      And she is told the withdrawal exceeds her balance

  Rule: Withdrawals must be in multiples the machine can dispense

    Scenario Outline: Amount not dispensable is rejected
      When Alice attempts to withdraw £<amount>
      Then nothing is dispensed
      And she is told to request a multiple of £10

      Examples:
        | amount |
        | 15     |
        | 99     |

  Rule: Every dispensed withdrawal is recorded

    Scenario: Statement records the withdrawal
      Given Alice withdrew £80 yesterday
      When she requests a statement
      Then the statement contains:
        | date      | description     | amount | balance |
        | yesterday | cash withdrawal | -£80   | £20     |
