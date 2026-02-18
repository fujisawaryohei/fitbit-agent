CREATE TABLE activity_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    record_date DATE NOT NULL,
    steps INTEGER,
    calories_burned INTEGER,
    active_minutes INTEGER,
    CONSTRAINT fk_activity_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uk_activity_records_user_date UNIQUE (user_id, record_date)
);
