from decimal import ROUND_HALF_EVEN, Decimal

DEFAULT_TAX_RATE = Decimal("0.20")


def line_total(quantity: int, unit_price: Decimal) -> Decimal:
    return Decimal(quantity) * unit_price


def invoice_total(lines: list[tuple[int, Decimal]], tax_rate: Decimal = DEFAULT_TAX_RATE) -> Decimal:
    net = sum((line_total(q, p) for q, p in lines), Decimal("0"))
    gross = net * (Decimal("1") + tax_rate)
    return gross.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
