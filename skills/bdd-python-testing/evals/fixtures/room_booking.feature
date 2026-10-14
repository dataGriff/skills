Feature: Meeting room booking
  As an office manager
  I want colleagues to book meeting rooms themselves
  so that rooms get used without double bookings.

  Background:
    Given the following rooms:
      | name    | capacity |
      | Mercury | 4        |
      | Venus   | 10       |

  Rule: A slot can only be booked once

    Scenario: Booking a free slot
      When Priya books Mercury for 10:00
      Then the booking is confirmed
      And Mercury is unavailable at 10:00

    Scenario: Booking an occupied slot is refused
      Given Dev has booked Mercury for 10:00
      When Priya attempts to book Mercury for 10:00
      Then the booking is refused because of "slot taken"

  Rule: A booking must fit the room

    Scenario: Booking beyond the room capacity is refused
      When Priya attempts to book Mercury for 14:00 with 6 attendees
      Then the booking is refused because of "over capacity"
