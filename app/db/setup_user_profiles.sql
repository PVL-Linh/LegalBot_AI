-- Bước 1: Thêm cột password_hash vào user_profiles
ALTER TABLE public.user_profiles 
ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Bước 2: Thêm cột email vào user_profiles (để bypass mode)
ALTER TABLE public.user_profiles 
ADD COLUMN IF NOT EXISTS email TEXT UNIQUE;

-- Bước 3: Enable RLS cho user_profiles
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Bước 4: Policies
DROP POLICY IF EXISTS "Public read access" ON public.user_profiles;
DROP POLICY IF EXISTS "Public insert access" ON public.user_profiles;
DROP POLICY IF EXISTS "Users can update own data" ON public.user_profiles;

CREATE POLICY "Public read access"
    ON public.user_profiles FOR SELECT USING (true);

CREATE POLICY "Public insert access"
    ON public.user_profiles FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update own data"
    ON public.user_profiles FOR UPDATE
    USING (auth.uid() = id);

-- Bước 5: Indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON public.user_profiles(email);

-- Bước 6: Grants
GRANT ALL ON public.user_profiles TO anon;
GRANT ALL ON public.user_profiles TO authenticated;
GRANT ALL ON public.user_profiles TO service_role;

-- Bước 7: Kiểm tra structure
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'user_profiles' 
AND table_schema = 'public';
