CREATE TABLE nutrition_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    record_date DATE NOT NULL,
    calories_intake INTEGER,
    water_ml INTEGER,
    CONSTRAINT fk_nutrition_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uk_nutrition_records_user_date UNIQUE (user_id, record_date)
);
