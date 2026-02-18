CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fitbit_user_id VARCHAR(64) NOT NULL,
    display_name VARCHAR(255),
    gender VARCHAR(16),
    height_cm DECIMAL(5,1),
    date_of_birth DATE,
    activity_level VARCHAR(32),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uk_users_fitbit_user_id UNIQUE(fitbit_user_id)
);