"""Gift card domain used by the BDD eval tasks. Do not modify."""


class RedemptionRefused(Exception):
    """Raised when a redemption cannot be applied to the card."""

    def __init__(self, reason):
        super().__init__(reason)
        self.reason = reason


class GiftCard:
    def __init__(self, balance, expired=False):
        self.balance = balance
        self.expired = expired

    def redeem(self, amount):
        if self.expired:
            raise RedemptionRefused("card expired")
        if amount > self.balance:
            raise RedemptionRefused("insufficient balance")
        self.balance -= amount
        return amount
