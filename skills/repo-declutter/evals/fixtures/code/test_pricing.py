import unittest
from decimal import Decimal

from pricing import calc, receipt_line, tax


class PricingTests(unittest.TestCase):
    def test_plain_discount(self):
        self.assertEqual(calc(10000, Decimal("0.10"), False), 9000)

    def test_first_order_bonus(self):
        self.assertEqual(calc(10000, Decimal("0.10"), True), 8500)

    def test_rate_is_capped(self):
        self.assertEqual(calc(10000, Decimal("0.90"), False), 4000)

    def test_rounds_half_even(self):
        self.assertEqual(calc(1001, Decimal("0.5"), False), 500)

    def test_tax(self):
        self.assertEqual(tax(1000, 2000), 200)

    def test_receipt_masks_card(self):
        self.assertEqual(receipt_line("4111111111111111", 999), "card ****1111 999")


if __name__ == "__main__":
    unittest.main()
