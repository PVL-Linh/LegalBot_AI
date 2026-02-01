-- Xóa bảng users (không dùng nữa)
-- Chỉ chạy sau khi đã migrate sang user_profiles!

-- Bước 1: Drop indexes
DROP INDEX IF EXISTS public.idx_users_email;
DROP INDEX IF EXISTS public.idx_users_created_at;

-- Bước 2: Drop policies
DROP POLICY IF EXISTS "Public read access" ON public.users;
DROP POLICY IF EXISTS "Public insert access" ON public.users;
DROP POLICY IF EXISTS "Users can update own data" ON public.users;

-- Bước 3: Drop table
DROP TABLE IF EXISTS public.users CASCADE;

-- Kiểm tra bảng còn tồn tại không
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name = 'users';
-- Kết quả: Không có rows = Đã xóa thành công!

-- Kiểm tra user_profiles có data không
SELECT COUNT(*) as total_users, 
       COUNT(CASE WHEN password_hash IS NOT NULL THEN 1 END) as users_with_password
FROM public.user_profiles;
