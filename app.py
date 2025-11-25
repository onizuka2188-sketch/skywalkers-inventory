import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import os
import shutil

# --- 설정 ---
CLOTHES_SIZES = ["S", "M", "L", "XL", "2XL", "3XL", "4XL", "Free"]
SHOE_SIZES = [str(s) for s in range(250, 325, 5)]
STAFF_ROLES = ["감독", "수석코치", "코치", "트레이너", "전력분석", "통역", "매니저", "닥터"]
CATEGORIES = ["전체보기", "하계용품", "동계용품", "연습복", "유니폼", "양말", "신발"]
MEMO_CATS = ["팀 연혁", "드래프트", "트레이드", "입/퇴사", "부상/재활", "기타 비고"]
DB_FILENAME = "skywalkers_data.db"

# 폴더 생성
if not os.path.exists("item_images"): os.makedirs("item_images")
if not os.path.exists("profile_images"): os.makedirs("profile_images")

# --- 페이지 설정 (탭 이름, 아이콘 등) ---
st.set_page_config(
    page_title="현대캐피탈 스카이워커스 용품 관리",
    page_icon="🏐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 스타일(CSS) 커스텀: 현대캐피탈 블루 ---
st.markdown("""
    <style>
    .stApp {background-color: #f8f9fa;}
    .main-header {font-size: 30px; font-weight: bold; color: #003399;}
    .sub-header {font-size: 18px; color: #555;}
    div.stButton > button:first-child {background-color: #003399; color: white;}
    </style>
    """, unsafe_allow_html=True)

# --- DB 함수 ---
def init_db():
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS players (id INTEGER PRIMARY KEY, name TEXT, back_number TEXT, top_size TEXT, bottom_size TEXT, shoe_size TEXT, image_path TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY, name TEXT, role TEXT, top_size TEXT, bottom_size TEXT, shoe_size TEXT, image_path TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY, date TEXT, category TEXT, item_name TEXT, size TEXT, quantity INTEGER DEFAULT 0, image_path TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, date TEXT, target_type TEXT, target_name TEXT, item_name TEXT, size TEXT, quantity INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS inbound_logs (id INTEGER PRIMARY KEY, date TEXT, category TEXT, item_name TEXT, size TEXT, quantity INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS memos (id INTEGER PRIMARY KEY, date TEXT, category TEXT, content TEXT)')
    conn.commit()
    conn.close()

def run_query(query, params=(), fetch=True):
    conn = sqlite3.connect(DB_FILENAME)
    c = conn.cursor()
    c.execute(query, params)
    if fetch:
        data = c.fetchall()
        conn.close()
        return data
    else:
        conn.commit()
        conn.close()
        return None

def get_dataframe(query, params=()):
    conn = sqlite3.connect(DB_FILENAME)
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

# --- 메인 앱 로직 ---
def main():
    init_db()

    # 사이드바 (메뉴)
    with st.sidebar:
        st.title("SKYWALKERS")
        st.subheader("용품 관리 시스템")
        menu = st.radio("메뉴 선택", ["🎁 지급 하기", "📦 재고 관리", "🏐 선수 명단", "👔 스텝 명단", "📋 전체 내역", "📝 비고/연혁"])
        st.write("---")
        st.caption(f"Manager: 유영욱 | {datetime.now().strftime('%Y-%m-%d')}")

    # 헤더
    st.markdown('<div class="main-header">SKYWALKERS EQUIPMENT MANAGER</div>', unsafe_allow_html=True)

    # 메뉴별 화면 연결
    if menu == "🎁 지급 하기":
        page_distribute()
    elif menu == "📦 재고 관리":
        page_inventory()
    elif menu == "🏐 선수 명단":
        page_players()
    elif menu == "👔 스텝 명단":
        page_staff()
    elif menu == "📋 전체 내역":
        page_history()
    elif menu == "📝 비고/연혁":
        page_memo()

# 1. 지급 페이지
def page_distribute():
    st.markdown("### 🚀 물품 지급 처리")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        target_type = st.selectbox("대상 구분", ["선수", "스텝"])
        
        # 이름 목록 불러오기
        if target_type == "선수":
            names = [r[0] for r in run_query("SELECT name FROM players")]
        else:
            names = [r[0] for r in run_query("SELECT name FROM staff")]
            
        target_name = st.selectbox("이름 선택", names if names else ["등록된 인원 없음"])
        
        # 선택된 사람 정보 보여주기
        if target_name and target_name != "등록된 인원 없음":
            if target_type == "선수":
                info = run_query("SELECT back_number, top_size, bottom_size, shoe_size FROM players WHERE name=?", (target_name,))
                if info:
                    st.info(f"**No.{info[0][0]} {target_name}**\n\n👕 상의: {info[0][1]} | 👖 하의: {info[0][2]} | 👟 신발: {info[0][3]}")
            else:
                info = run_query("SELECT role, top_size, bottom_size, shoe_size FROM staff WHERE name=?", (target_name,))
                if info:
                    st.info(f"**{info[0][0]} {target_name}**\n\n👕 상의: {info[0][1]} | 👖 하의: {info[0][2]} | 👟 신발: {info[0][3]}")

    with col2:
        st.write("#### 지급할 물품")
        cat_filter = st.radio("카테고리 필터", CATEGORIES, horizontal=True)
        
        # 물품 목록 불러오기
        if cat_filter == "전체보기":
            items = [r[0] for r in run_query("SELECT DISTINCT item_name FROM inventory")]
        else:
            items = [r[0] for r in run_query("SELECT DISTINCT item_name FROM inventory WHERE category=?", (cat_filter,))]
            
        selected_item = st.selectbox("품목 선택", items if items else ["재고 없음"])
        
        if selected_item and selected_item != "재고 없음":
            # 사이즈 및 재고 불러오기
            if cat_filter == "전체보기":
                 stock_data = run_query("SELECT size, quantity, category FROM inventory WHERE item_name=?", (selected_item,))
            else:
                 stock_data = run_query("SELECT size, quantity, category FROM inventory WHERE item_name=? AND category=?", (selected_item, cat_filter))
            
            # 옵션 만들기: "L (남은수량: 5)" 형식
            size_opts = {f"{r[0]} (재고: {r[1]})": (r[0], r[1], r[2]) for r in stock_data}
            selected_size_opt = st.selectbox("사이즈 선택", list(size_opts.keys()))
            
            qty_to_give = st.number_input("지급 수량", min_value=1, value=1)
            
            if st.button("지급 확정"):
                real_size, current_qty, real_cat = size_opts[selected_size_opt]
                if current_qty >= qty_to_give:
                    # DB 업데이트
                    run_query("UPDATE inventory SET quantity=? WHERE item_name=? AND size=? AND category=?", 
                              (current_qty - qty_to_give, selected_item, real_size, real_cat), fetch=False)
                    run_query("INSERT INTO logs (date, target_type, target_name, item_name, size, quantity) VALUES (?,?,?,?,?,?)",
                              (datetime.now().strftime("%Y-%m-%d"), target_type, target_name, selected_item, real_size, qty_to_give), fetch=False)
                    st.success(f"{target_name}님에게 {selected_item}({real_size}) {qty_to_give}개 지급 완료!")
                    st.rerun()
                else:
                    st.error("재고가 부족합니다!")

# 2. 재고 관리 페이지
def page_inventory():
    st.markdown("### 📦 재고 입고 및 관리")
    
    with st.expander("➕ 새 물품 입고하기 (클릭해서 열기)"):
        col1, col2 = st.columns(2)
        with col1:
            i_date = st.date_input("입고 날짜", datetime.now())
            i_cat = st.selectbox("카테고리", CATEGORIES[1:]) # 전체보기 제외
            i_name = st.text_input("품명 (예: 반팔티셔츠)")
        with col2:
            if i_cat == "신발":
                i_size = st.selectbox("사이즈", SHOE_SIZES)
            else:
                i_size = st.selectbox("사이즈", CLOTHES_SIZES)
            i_qty = st.number_input("수량", min_value=1, value=10)
            i_img = st.file_uploader("이미지 (선택)", type=['png', 'jpg', 'jpeg'])
            
        if st.button("입고 저장"):
            if i_name:
                # 이미지 저장 처리
                img_path = ""
                if i_img:
                    save_dir = "item_images"
                    file_path = os.path.join(save_dir, i_img.name)
                    with open(file_path, "wb") as f:
                        f.write(i_img.getbuffer())
                    img_path = file_path
                
                # 재고 확인 및 업데이트
                exist = run_query("SELECT id, quantity FROM inventory WHERE item_name=? AND size=? AND category=?", (i_name, i_size, i_cat))
                if exist:
                    run_query("UPDATE inventory SET quantity=?, image_path=? WHERE id=?", 
                              (exist[0][1] + i_qty, img_path if img_path else None, exist[0][0]), fetch=False)
                else:
                    run_query("INSERT INTO inventory (date, category, item_name, size, quantity, image_path) VALUES (?,?,?,?,?,?)",
                              (i_date.strftime("%Y-%m-%d"), i_cat, i_name, i_size, i_qty, img_path), fetch=False)
                
                # 입고 로그
                run_query("INSERT INTO inbound_logs (date, category, item_name, size, quantity) VALUES (?,?,?,?,?)",
                          (i_date.strftime("%Y-%m-%d"), i_cat, i_name, i_size, i_qty), fetch=False)
                
                st.success(f"{i_name} 입고 완료!")
                st.rerun()
            else:
                st.warning("품명을 입력해주세요.")

    st.write("---")
    st.write("#### 📊 현재 재고 현황")
    
    # 필터
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        view_cat = st.selectbox("카테고리별 보기", CATEGORIES)
    with col_f2:
        search_txt = st.text_input("품명 검색")
        
    # 데이터 조회
    sql = "SELECT id, category as '구분', item_name as '품명', size as '사이즈', quantity as '수량' FROM inventory WHERE 1=1"
    params = []
    if view_cat != "전체보기":
        sql += " AND category=?"
        params.append(view_cat)
    if search_txt:
        sql += " AND item_name LIKE ?"
        params.append(f"%{search_txt}%")
        
    df = get_dataframe(sql, params)
    
    # 데이터프레임 표시 (수정 가능하게 하거나 삭제 버튼 추가는 복잡하니 조회 위주로)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 삭제 기능
    with st.expander("🗑️ 재고 삭제 (주의!)"):
        del_id = st.number_input("삭제할 재고의 ID 번호를 입력하세요", min_value=0, step=1)
        if st.button("선택한 ID 삭제"):
            run_query("DELETE FROM inventory WHERE id=?", (del_id,), fetch=False)
            st.warning(f"ID {del_id} 삭제됨")
            st.rerun()

# 3. 선수 명단
def page_players():
    st.markdown("### 🏐 선수 명단 관리")
    
    with st.expander("➕ 선수 등록하기"):
        c1, c2, c3 = st.columns(3)
        p_num = c1.text_input("배번")
        p_name = c2.text_input("이름")
        p_shoe = c3.selectbox("신발 사이즈", SHOE_SIZES)
        c4, c5 = st.columns(2)
        p_top = c4.selectbox("상의 사이즈", CLOTHES_SIZES)
        p_bot = c5.selectbox("하의 사이즈", CLOTHES_SIZES)
        
        if st.button("선수 저장"):
            if p_name:
                run_query("INSERT INTO players (name, back_number, top_size, bottom_size, shoe_size) VALUES (?,?,?,?,?)",
                          (p_name, p_num, p_top, p_bot, p_shoe), fetch=False)
                st.success(f"{p_name} 선수 등록 완료")
                st.rerun()
    
    df = get_dataframe("SELECT id, back_number as '배번', name as '이름', top_size as '상의', bottom_size as '하의', shoe_size as '신발' FROM players ORDER BY back_number")
    st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("🗑️ 선수 삭제"):
        del_name = st.selectbox("삭제할 선수 선택", df['이름'].tolist())
        if st.button("선수 삭제"):
            run_query("DELETE FROM players WHERE name=?", (del_name,), fetch=False)
            st.success("삭제되었습니다.")
            st.rerun()

# 4. 스텝 명단
def page_staff():
    st.markdown("### 👔 스텝 명단 관리")
    
    with st.expander("➕ 스텝 등록하기"):
        c1, c2 = st.columns(2)
        s_role = c1.selectbox("직책", STAFF_ROLES)
        s_name = c2.text_input("이름 ")
        c3, c4, c5 = st.columns(3)
        s_top = c3.selectbox("상의", CLOTHES_SIZES, key="st")
        s_bot = c4.selectbox("하의", CLOTHES_SIZES, key="sb")
        s_shoe = c5.selectbox("신발", SHOE_SIZES, key="ss")
        
        if st.button("스텝 저장"):
            if s_name:
                run_query("INSERT INTO staff (name, role, top_size, bottom_size, shoe_size) VALUES (?,?,?,?,?)",
                          (s_name, s_role, s_top, s_bot, s_shoe), fetch=False)
                st.success("등록 완료")
                st.rerun()

    df = get_dataframe("SELECT id, role as '직책', name as '이름', top_size as '상의', bottom_size as '하의', shoe_size as '신발' FROM staff ORDER BY role")
    st.dataframe(df, use_container_width=True, hide_index=True)

# 5. 전체 내역
def page_history():
    st.markdown("### 📋 입출고 내역")
    
    tab1, tab2 = st.tabs(["📤 지급(출고) 내역", "📥 입고 내역"])
    
    with tab1:
        h_name = st.text_input("이름 검색 (지급 내역)", key="h_out")
        sql = "SELECT id, date as '날짜', target_type as '구분', target_name as '이름', item_name as '품명', size as '사이즈', quantity as '수량' FROM logs WHERE 1=1"
        if h_name:
            sql += f" AND target_name LIKE '%{h_name}%'"
        sql += " ORDER BY id DESC"
        
        df_out = get_dataframe(sql)
        st.dataframe(df_out, use_container_width=True, hide_index=True)
        
        if st.button("선택 내역 반납 처리 (가장 최근 것 1개)"):
            # 단순화를 위해 로직 간소화 (실제로는 ID 선택이 필요함)
            st.info("웹 버전에서는 ID를 확인하여 DB 관리자에게 문의하거나 추후 업데이트될 삭제 기능을 이용해주세요.")

    with tab2:
        col1, col2 = st.columns(2)
        in_date = col1.text_input("날짜 검색 (YYYY-MM-DD)")
        in_item = col2.text_input("품명 검색")
        
        sql_in = "SELECT id, date as '날짜', category as '구분', item_name as '품명', size as '사이즈', quantity as '수량' FROM inbound_logs WHERE 1=1"
        if in_date: sql_in += f" AND date LIKE '%{in_date}%'"
        if in_item: sql_in += f" AND item_name LIKE '%{in_item}%'"
        sql_in += " ORDER BY id DESC"
        
        df_in = get_dataframe(sql_in)
        st.dataframe(df_in, use_container_width=True, hide_index=True)
        
        # 입고 내역 삭제 구현
        st.write("---")
        del_ids = st.multiselect("삭제할 입고 내역 ID 선택", df_in['id'].tolist())
        if st.button("선택한 입고 내역 삭제"):
            for did in del_ids:
                run_query("DELETE FROM inbound_logs WHERE id=?", (did,), fetch=False)
            st.success("삭제 완료")
            st.rerun()

# 6. 비고/연혁
def page_memo():
    st.markdown("### 📝 비고 및 연혁")
    
    with st.form("memo_form"):
        c1, c2 = st.columns([1, 2])
        m_date = c1.date_input("날짜")
        m_cat = c2.selectbox("구분", MEMO_CATS)
        m_content = st.text_area("내용")
        if st.form_submit_button("기록 저장"):
            run_query("INSERT INTO memos (date, category, content) VALUES (?,?,?)", 
                      (m_date.strftime("%Y-%m-%d"), m_cat, m_content), fetch=False)
            st.success("저장됨")
            st.rerun()
            
    df = get_dataframe("SELECT id, date as '날짜', category as '구분', content as '내용' FROM memos ORDER BY date DESC")
    st.dataframe(df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()