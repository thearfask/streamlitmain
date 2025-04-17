import streamlit as st
import sqlite3
from datetime import datetime
import json
import os

# 建立資料庫連線
conn = sqlite3.connect('social_app.db', check_same_thread=False)
c = conn.cursor()

# 建立資料表（如果不存在）
c.execute('''CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT,
                author TEXT,
                timestamp TEXT,
                likes INTEGER,
                comments TEXT,
                category TEXT,
                image_path TEXT
            )''')
conn.commit()

# 預設 admin 清單
ADMIN_USERS = ["Arfaa", "Sanny"]

# 使用者登入名稱
if 'username' not in st.session_state:
    st.session_state.username = st.text_input("請輸入你的名稱 / Enter your name")
    st.stop()

# 判斷是否為 Admin
is_admin = st.session_state.username in ADMIN_USERS

# Sidebar 顯示登入者資訊
st.sidebar.success(f"👤 使用者：{st.session_state.username}")
if is_admin:
    st.sidebar.info("🛠️ 你是 Admin！")

# Header
st.title("📝 Mini Social Media / 迷你社群平台")
st.subheader("發佈你的貼文 / Share Your Thoughts")

# 分類清單（中英文對照）
categories = {
    "生活 Life": "生活 Life",
    "學習 Study": "學習 Study",
    "工作 Work": "工作 Work",
    "娛樂 Fun": "娛樂 Fun",
    "其他 Others": "其他 Others"
}

# 發文表單
with st.form("post_form"):
    content = st.text_area("你在想什麼？ / What's on your mind?", max_chars=280)
    category = st.selectbox("選擇分類 / Select Category", list(categories.values()))
    image = st.file_uploader("上傳圖片（選填）/ Upload Image (Optional)", type=["png", "jpg", "jpeg"])
    submitted = st.form_submit_button("發佈 / Post")

    if submitted and content:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        image_path = None
        if image is not None:
            image_folder = "uploaded_images"
            os.makedirs(image_folder, exist_ok=True)
            image_path = os.path.join(image_folder, f"{timestamp.replace(':', '-')}_{image.name}")
            with open(image_path, "wb") as f:
                f.write(image.read())

        c.execute("INSERT INTO posts (content, author, timestamp, likes, comments, category, image_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (content, st.session_state.username, timestamp, 0, json.dumps([]), category, image_path))
        conn.commit()
        if 'username' in st.session_state:
            st.rerun()

st.markdown("---")
st.subheader("📬 所有貼文 / All Posts")

search_keyword = st.text_input("🔍 搜尋貼文 / Search posts")

# 讀取所有貼文（由新到舊）
c.execute("SELECT * FROM posts ORDER BY id DESC")
rows = c.fetchall()

for row in rows:
    post_id, content, author, timestamp, likes, comments, category, image_path = row
    comments = json.loads(comments)

    if search_keyword and search_keyword.lower() not in content.lower():
        continue

    st.markdown(f"**🗓 {timestamp}**")
    author_label = "👑 " + author if author in ADMIN_USERS else author
    st.markdown(f"👤 {author_label} ｜ 🏷️ {category}")
    st.markdown(f"💬 {content}")

    if image_path and os.path.exists(image_path):
        st.image(image_path, use_column_width=True)

    col1, col2 = st.columns(2)

    # Like 按鈕
    if col1.button(f"👍 {likes}", key=f"like_{post_id}"):
        c.execute("UPDATE posts SET likes = likes + 1 WHERE id = ?", (post_id,))
        conn.commit()
        if 'username' in st.session_state:
            st.rerun()

    # 留言區
    comment_count = len(comments)
    with col2.expander(f"💭 留言 / Comments ({comment_count})"):
        with st.form(f"comment_form_{post_id}"):
            comment_text = st.text_input("留言內容 / Your comment", key=f"comment_input_{post_id}")
            send = st.form_submit_button("送出留言 / Submit")
            if send and comment_text:
                comments.append({"author": st.session_state.username, "content": comment_text})
                c.execute("UPDATE posts SET comments = ? WHERE id = ?", (json.dumps(comments), post_id))
                conn.commit()
                if 'username' in st.session_state:
                    st.rerun()

        for j, cmt in enumerate(comments):
            author_tag = "👑 " + cmt['author'] if cmt['author'] in ADMIN_USERS else cmt['author']
            st.markdown(f"- {author_tag}: {cmt['content']}")
            if is_admin:
                if st.button(f"刪除留言 / Delete", key=f"del_comment_{post_id}_{j}"):
                    comments.pop(j)
                    c.execute("UPDATE posts SET comments = ? WHERE id = ?", (json.dumps(comments), post_id))
                    conn.commit()
                    if 'username' in st.session_state:
                        st.rerun()

    # 刪除貼文（作者本人或 Admin）
    if is_admin or st.session_state.username == author:
        if st.button("🗑️ 刪除這則貼文 / Delete this post", key=f"delete_{post_id}"):
            c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
            conn.commit()
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
            if 'username' in st.session_state:
                st.rerun()

    st.markdown("---")
