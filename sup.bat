rem uv run  ./src/py_supabase/app01.py
rem uv run  streamlit run  ./src/py_supabase/app02_todos.py
rem uv run ./test/test_mongo.py

uv run  streamlit run  ./src/py_supabase/app03_mongo.py  --server.port 3200
