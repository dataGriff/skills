// Shopping cart pricing, as signed off by the business:
// - the subtotal is the sum of item price x quantity, in pence
// - a 10% discount applies to subtotals of £100.00 or more, before delivery
// - orders of £50.00 or more (after any discount) ship free;
//   otherwise delivery costs £4.99
// All amounts are integer pence.

const DISCOUNT_THRESHOLD = 100_00;
const FREE_DELIVERY_THRESHOLD = 50_00;
const DELIVERY_CHARGE = 4_99;

class Cart {
  constructor() {
    this.items = [];
  }

  add(name, pricePence, quantity = 1) {
    this.items.push({ name, pricePence, quantity });
  }

  subtotal() {
    return this.items.reduce(
      (sum, item) => sum + item.pricePence * item.quantity,
      0
    );
  }

  discount() {
    const subtotal = this.subtotal();
    return subtotal >= DISCOUNT_THRESHOLD ? Math.round(subtotal * 0.1) : 0;
  }

  deliveryCharge() {
    const goods = this.subtotal() - this.discount();
    return goods >= FREE_DELIVERY_THRESHOLD || goods === 0
      ? 0
      : DELIVERY_CHARGE;
  }

  total() {
    return this.subtotal() - this.discount() + this.deliveryCharge();
  }
}

module.exports = { Cart };
