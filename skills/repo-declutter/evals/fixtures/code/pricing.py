# SPDX-License-Identifier: MIT
# Copyright (c) 2024 Acme Ledger Ltd. See LICENSE for terms.
"""Pricing rules for the ledger checkout."""
from decimal import ROUND_HALF_EVEN, Decimal

# ==============================================================
# ======================= PRICING ==============================
# ==============================================================
# added by jsmith 2020-03-04
# modified by rlee on 2021-11-02

FIRST_ORDER_BONUS = Decimal("0.05")  # the first order bonus rate
MAX_RATE = Decimal("0.60")  # the maximum rate

# def old_calc(d, r):
#     total = d - (d * r)
#     if total < 0:
#         total = 0
#     return int(total)

# TODO(2021): remove after v2 migration


def calc(d, r, f):
    # d = subtotal in minor units, r = discount rate, f = first order
    # increment the rate if first order
    if f:
        r = r + FIRST_ORDER_BONUS
    # cap the rate
    if r > MAX_RATE:
        r = MAX_RATE
    # compute the discounted amount
    amount = Decimal(d) * (Decimal(1) - r)
    # Round half-even: ledger reconciliation needs banker's rounding (FIN-212)
    rounded = amount.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)
    # return the total
    return int(rounded)


def tax(amount_minor, rate_bps):
    # multiply the amount by the rate in basis points and divide by 10000
    t = Decimal(amount_minor) * Decimal(rate_bps) / Decimal(10000)
    # Round half-even (FIN-212)
    return int(t.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN))


def receipt_line(card_token, amount_minor):
    # never log card_token: PCI scope (SEC-7); only the last four digits may appear
    last4 = card_token[-4:]
    # build the line
    line = f"card ****{last4} {amount_minor}"
    # return the line
    return line
