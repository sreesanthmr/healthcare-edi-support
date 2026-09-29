CREATE TABLE members (
    id SERIAL PRIMARY KEY,
    member_id VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(10),
    health_plan VARCHAR(100),
    effective_date DATE,
    source_file VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE file_processing_log (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    status VARCHAR(30) NOT NULL,
    record_count INTEGER DEFAULT 0,
    error_message TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);