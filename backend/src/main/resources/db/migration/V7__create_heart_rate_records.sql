CREATE TABLE heart_rate_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    record_date DATE NOT NULL,
    resting_hr INTEGER,
    CONSTRAINT fk_heart_rate_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uk_heart_rate_records_user_date UNIQUE (user_id, record_date)
);
