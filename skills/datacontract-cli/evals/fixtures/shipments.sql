CREATE TABLE shipments (
    shipment_id UUID NOT NULL PRIMARY KEY,
    order_id UUID NOT NULL,
    carrier VARCHAR(50) NOT NULL,
    tracking_number VARCHAR(100),
    shipped_at TIMESTAMPTZ NOT NULL,
    delivered_at TIMESTAMPTZ,
    weight_kg NUMERIC(8,2),
    status VARCHAR(20) NOT NULL
);
