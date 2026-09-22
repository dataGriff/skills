"""Formatting helpers shared by the API handlers."""


def format_widget(raw):
    """Normalise a raw catalogue entry into the public JSON shape."""
    return {
        "id": raw["id"],
        "name": raw["name"].strip(),
        "price_cents": int(round(float(raw["price"]) * 100)),
        "tags": sorted(set(raw.get("tags", []))),
    }


def legacy_format(raw):
    """Pre-0.3 JSON shape (price as a float string). Used by the sync worker."""
    return {
        "id": raw["id"],
        "name": raw["name"],
        "price": "%.2f" % float(raw["price"]),
    }


def slugify(name):
    """Lower-case, hyphen-separated form of a widget name."""
    return "-".join(name.lower().split())
