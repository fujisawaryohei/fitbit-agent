CREATE TABLE sleep_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    record_date DATE NOT NULL,
    total_minutes INTEGER,
    deep_minutes INTEGER,
    light_minutes INTEGER,
    rem_minutes INTEGER,
    wake_minutes INTEGER,
    CONSTRAINT fk_sleep_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uk_sleep_records_user_date UNIQUE (user_id, record_date)
);
