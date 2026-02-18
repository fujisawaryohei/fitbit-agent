CREATE TABLE body_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    record_date DATE NOT NULL,
    weight_kg DECIMAL(5,2),
    body_fat_pct DECIMAL(4,1),
    bmi DECIMAL(4,1),
    CONSTRAINT fk_body_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uk_body_records_user_date UNIQUE (user_id, record_date)
);
