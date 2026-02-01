-- Bước 1: Thêm cột password vào bảng users
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS password_hash TEXT;

-- Bước 2: Update user hiện có với password mặc định (cho test)
-- Password: "123456" đã hash
UPDATE public.users 
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5nyvXJCdW8I3u'
WHERE password_hash IS NULL;

-- Kiểm tra
SELECT id, email, password_hash IS NOT NULL as has_password FROM public.users;
