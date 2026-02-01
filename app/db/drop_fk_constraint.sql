-- Xóa constraint FK giữa user_profiles và auth.users
-- Để cho phép tạo user bypass mode (không có trong auth.users)

DO $$ 
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE constraint_name = 'user_profiles_id_fkey') THEN
    ALTER TABLE public.user_profiles DROP CONSTRAINT user_profiles_id_fkey;
  END IF;
END $$;

-- Verify
SELECT constraint_name 
FROM information_schema.table_constraints 
WHERE table_name = 'user_profiles' 
  AND constraint_type = 'FOREIGN KEY';
