-- =============================================================================
-- Enterprise Agentic Knowledge Platform (EAKP) Database Initialization Script
-- Extensions: pgvector, pg_trgm
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- -----------------------------------------------------------------------------
-- Unstructured Knowledge Store (RAG Documents & Chunks)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id VARCHAR(255) NOT NULL,
    doc_title VARCHAR(500),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(1536), -- Default for text-embedding-3-small or custom dimensions
    tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indices for Hybrid Search
-- 1. HNSW index for fast Cosine Distance dense vector search
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding 
    ON document_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- 2. GIN index for Sparse Full-text Search
CREATE INDEX IF NOT EXISTS idx_document_chunks_tsv 
    ON document_chunks USING gin (tsv);

-- 3. B-Tree index for document tracking & metadata filtering
CREATE INDEX IF NOT EXISTS idx_document_chunks_doc_id 
    ON document_chunks (doc_id);

CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata 
    ON document_chunks USING gin (metadata);


-- -----------------------------------------------------------------------------
-- Structured Mock Business DB (ERP / E-Commerce) for Text-to-SQL Agent
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(50) DEFAULT 'STANDARD', -- STANDARD, VIP, ENTERPRISE
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    category_id INT REFERENCES categories(id),
    name VARCHAR(200) NOT NULL,
    sku VARCHAR(50) UNIQUE NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    stock INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    total_amount NUMERIC(12, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'COMPLETED', -- PENDING, COMPLETED, CANCELLED
    order_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id),
    quantity INT NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL
);

-- Seed sample data for immediate Text-to-SQL testing
INSERT INTO categories (name, description) VALUES
('Hardware & Servers', 'Server components, enterprise storage and networking equipment'),
('Cloud Licenses', 'SaaS subscriptions and enterprise cloud software solutions'),
('Security Solutions', 'Firewalls, endpoint security, and compliance tooling')
ON CONFLICT DO NOTHING;

INSERT INTO users (name, email, tier) VALUES
('Nguyen Van A', 'nguyen.a@enterprise.vn', 'VIP'),
('Tran Thi B', 'tran.b@fintech.com', 'ENTERPRISE'),
('Le Van C', 'le.c@retail.vn', 'STANDARD')
ON CONFLICT DO NOTHING;
