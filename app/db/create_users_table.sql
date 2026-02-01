-- Xóa bảng cũ nếu có (để reset policies)
DROP TABLE IF EXISTS public.users CASCADE;

-- Tạo bảng users mới
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Enable RLS
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Policy 1: SELECT - Ai cũng đọc được
CREATE POLICY "Public read access"
    ON public.users
    FOR SELECT
    USING (true);

-- Policy 2: INSERT - Ai cũng tạo được (BYPASS MODE)
CREATE POLICY "Public insert access"
    ON public.users
    FOR INSERT
    WITH CHECK (true);

-- Policy 3: UPDATE - Chỉ user mới update được data của mình
CREATE POLICY "Users can update own data"
    ON public.users
    FOR UPDATE
    USING (auth.uid() = id);

-- Index cho performance
CREATE INDEX idx_users_email ON public.users(email);
CREATE INDEX idx_users_created_at ON public.users(created_at);

-- Grant permissions đầy đủ
GRANT ALL ON public.users TO anon;
GRANT ALL ON public.users TO authenticated;
GRANT ALL ON public.users TO service_role;
