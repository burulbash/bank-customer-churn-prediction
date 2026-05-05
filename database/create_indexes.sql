CREATE INDEX idx_products_client_id ON raw.products(client_id);
CREATE INDEX idx_products_client_open_date ON raw.products(client_id, open_date);
CREATE INDEX idx_products_client_close_date ON raw.products(client_id, close_date);

CREATE INDEX idx_transactions_client_date ON raw.transactions(client_id, transaction_date);
CREATE INDEX idx_transactions_date ON raw.transactions(transaction_date);
CREATE INDEX idx_transactions_type ON raw.transactions(transaction_type);
CREATE INDEX idx_transactions_channel ON raw.transactions(channel);

CREATE INDEX idx_app_events_client_date ON raw.app_events(client_id, event_date);
CREATE INDEX idx_app_events_date ON raw.app_events(event_date);
CREATE INDEX idx_app_events_type ON raw.app_events(event_type);

CREATE INDEX idx_support_tickets_client_date ON raw.support_tickets(client_id, ticket_date);
CREATE INDEX idx_marketing_contacts_client_date ON raw.marketing_contacts(client_id, contact_date);
CREATE INDEX idx_customer_value_client_month ON raw.customer_value_monthly(client_id, month);

ANALYZE raw.clients;
ANALYZE raw.products;
ANALYZE raw.transactions;
ANALYZE raw.app_events;
ANALYZE raw.support_tickets;
ANALYZE raw.marketing_contacts;
ANALYZE raw.customer_value_monthly;
ANALYZE raw.macro_calendar;
