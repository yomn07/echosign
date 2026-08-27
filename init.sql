CREATE TABLE public.landmarks (
    id BIGSERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    landmarks JSONB NOT NULL
);
 
CREATE INDEX idx_landmarks_text
ON landmarks(text);
 
 
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    reset_token_expires TIMESTAMPTZ,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    reset_token_hash VARCHAR,
    verification_token VARCHAR,
    verification_expires_at TIMESTAMPTZ
);
 
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_id ON users(id);