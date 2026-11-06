a)  https://medium.com/@summer12126/supabase-postgres-journey-with-python-1789e8bbb53c

b) todos:
https://www.youtube.com/watch?v=ip87CHxtoJY
https://github.com/turtlecode/Build-a-To-Do-App-with-Python-Streamlit-Supabase-Full-Tutorial/blob/main/main.py





================== 1)  supabase ==============================

uv add supabase   python-dotenv  pandas

Data API info:  https://supabase.com/dashboard/project/ncoelrbozjgkihbelzmj/integrations/data_api/overview
Publishable Anon key info: https://supabase.com/dashboard/project/ncoelrbozjgkihbelzmj/settings/api-keys

to give access, run in the "sql editor":
         a)  GRANT SELECT ON public."tankerInfo" TO anon;
         b) GRANT USAGE ON SCHEMA public TO anon;                ------>  X
         c) CREATE POLICY "Allow anon read access" ON public."tankerInfo" FOR SELECT TO anon USING (true);  ----->  X


CREATE POLICY "Allow select for all" ON public.users for select using (true);

------ app02_todos -----------------
CREATE TABLE public.todos (
    id SERIAL PRIMARY KEY,
    task TEXT NOT NULL
);

GRANT SELECT ON public.todos TO anon;', 'details': None}


======== 2)  mongodb (cloud / atlas) =======================================

uv add bson pymongo

IP adding / access list: 
https://cloud.mongodb.com/v2/6aecbf42bedcc3f04ec4a01b#/security/network/accessList

users: 
https://cloud.mongodb.com/v2/6aecbf42bedcc3f04ec4a01b#/security/database/users



Couldn't connect to MongoDB. Check .streamlit/secrets.toml and that your IP address is allowed under Network Access in Atlas.

Details: bad auth : authentication failed, full error: {'ok': 0, 'errmsg': 'bad auth : authentication failed', 'code': 8000, 'codeName': 'AtlasError'}
but already added 0:0:0:0/0 in the Network Access in Atlas. how to fix? 