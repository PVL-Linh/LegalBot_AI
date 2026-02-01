-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (Supabase Auth tự động tạo, nhưng có thể extend)
CREATE TABLE public.user_profiles (
    id UUID REFERENCES auth.users PRIMARY KEY,
    username VARCHAR(100) UNIQUE,
    full_name VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user', -- 'user' or 'admin'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Conversations table
CREATE TABLE public.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    title VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Messages table
CREATE TABLE public.messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}', -- sources, confidence, tools_used
    created_at TIMESTAMP DEFAULT NOW()
);

-- Legal documents table
CREATE TABLE public.legal_documents (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    document_number VARCHAR(100),
    category VARCHAR(100),
    issued_date DATE,
    effective_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    file_url TEXT, -- Supabase Storage URL
    content TEXT,
    summary TEXT,
    pinecone_synced BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

-- Document chunks metadata (Pinecone stores vectors)
CREATE TABLE public.document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT REFERENCES public.legal_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER,
    chunk_text TEXT,
    pinecone_id VARCHAR(255), -- ID in Pinecone
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Analytics table
CREATE TABLE public.analytics (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(100), -- 'query', 'document_generated', etc.
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Feedback table
CREATE TABLE public.feedback (
    id BIGSERIAL PRIMARY KEY,
    message_id BIGINT REFERENCES public.messages(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_conversations_user_id ON public.conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON public.messages(conversation_id);
CREATE INDEX idx_messages_created_at ON public.messages(created_at DESC);
CREATE INDEX idx_legal_documents_category ON public.legal_documents(category);
CREATE INDEX idx_legal_documents_status ON public.legal_documents(status);
CREATE INDEX idx_document_chunks_document_id ON public.document_chunks(document_id);
CREATE INDEX idx_analytics_event_type ON public.analytics(event_type);
CREATE INDEX idx_analytics_created_at ON public.analytics(created_at DESC);

-- Row Level Security (RLS) Policies
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;

-- Users can only read their own profile
CREATE POLICY "Users can view own profile" 
    ON public.user_profiles FOR SELECT 
    USING (auth.uid() = id);

-- Users can only access their own conversations
CREATE POLICY "Users can view own conversations" 
    ON public.conversations FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create own conversations" 
    ON public.conversations FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

-- Users can view messages in their conversations
CREATE POLICY "Users can view own messages" 
    ON public.messages FOR SELECT 
    USING (
        conversation_id IN (
            SELECT id FROM public.conversations 
            WHERE user_id = auth.uid()
        )
    );

-- Admin can view everything
CREATE POLICY "Admins can view all" 
    ON public.legal_documents FOR ALL 
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );
