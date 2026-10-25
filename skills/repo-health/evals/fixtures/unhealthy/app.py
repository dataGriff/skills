import json
import os
import time
import urllib.request
from decimal import Decimal

from billing import invoice_total

RETRY_LIMIT = 7
BATCH_SIZE = 250


def settings():
    return {
        "db_url": os.environ["INVOICER_DB_URL"],
        "api_key": os.environ["PAYMENT_API_KEY"],
        "tax_rate": Decimal(os.getenv("INVOICER_TAX_RATE", "0.20")),
        "pdf": os.getenv("INVOICER_ENABLE_PDF", "false") == "true",
    }


# def push_legacy(invoice, api_key):
#     body = json.dumps(invoice).encode()
#     return urllib.request.urlopen(LEGACY_URL, data=body)


def push(invoice: dict, api_key: str) -> None:
    body = json.dumps(invoice).encode()
    request = urllib.request.Request(
        "https://api.payments.example.com/v2/invoices", data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    # TODO: handle 429 responses separately
    for attempt in range(RETRY_LIMIT):
        try:
            urllib.request.urlopen(request, timeout=10)
            return
        except OSError:
            time.sleep(2 ** attempt)
    raise RuntimeError("payments provider unreachable")


def run(customers: list[dict]) -> None:
    cfg = settings()
    for start in range(0, len(customers), BATCH_SIZE):
        for customer in customers[start:start + BATCH_SIZE]:
            total = invoice_total(customer["lines"], cfg["tax_rate"])
            push({"customer": customer["id"], "total": str(total), "pdf": cfg["pdf"]}, cfg["api_key"])


if __name__ == "__main__":
    run([])
