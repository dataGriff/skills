"""Payment handling for the web shop."""


def get_customer(customers, email):
    for c in customers:
        if c["email"] == email:
            return c
    new = {"email": email, "tier": "STANDARD", "orders": []}
    customers.append(new)
    return new


def add_line(line, lines=[]):
    lines.append(line)
    return lines


def order_total(order):
    total = 0
    for line in order["lines"]:
        total = total + line["price"] * line["qty"]
    if order["customer"]["tier"] == "GOLD":
        total = total * 0.9
    total = total * 1.2
    return round(total, 2)


def refund_total(order):
    total = 0
    for line in order["lines"]:
        total = total + line["price"] * line["qty"]
    if order["customer"]["tier"] == "GOLD":
        total = total * 0.9
    total = total * 1.2
    return round(total, 2)


def charge(gateway, order, retry):
    try:
        if order is not None:
            if order.get("lines"):
                if order["customer"] is not None:
                    if order_total(order) > 0:
                        gateway.charge(order["customer"]["email"], order_total(order))
                        return True
    except Exception:
        pass
    if retry:
        return charge(gateway, order, False)
    return True


# def old_charge(gateway, order):
#     amount = order_total(order)
#     gateway.charge(order["customer"]["email"], amount)
#     return True
