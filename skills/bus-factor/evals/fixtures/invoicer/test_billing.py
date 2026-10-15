import unittest
from decimal import Decimal

from billing import invoice_total, line_total


class BillingTest(unittest.TestCase):
    def test_line_total(self):
        self.assertEqual(line_total(3, Decimal("2.50")), Decimal("7.50"))

    def test_invoice_total_adds_tax(self):
        self.assertEqual(invoice_total([(1, Decimal("100"))]), Decimal("120.00"))

    def test_half_even_rounding(self):
        self.assertEqual(invoice_total([(1, Decimal("0.125"))], Decimal("0")), Decimal("0.12"))
