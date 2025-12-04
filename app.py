import os
import pandas as pd
import streamlit as st
import mysql.connector as mysql

# Optional .env support (safe to ignore if not installed)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ------------------ DB CONFIG ------------------
DB_CFG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "4421"),
    "database": os.getenv("DB_NAME", "immigrant_integration"),
    "autocommit": True,
}

# ------------------ DB HELPERS ------------------
@st.cache_resource(show_spinner=False)
def get_conn():
    return mysql.connect(**DB_CFG)

def run_select(sql, params=None):
    conn = get_conn()
    with conn.cursor(dictionary=True) as cur:
        cur.execute(sql, params or ())
        rows = cur.fetchall()
    return pd.DataFrame(rows)

def run_exec(sql, params=None):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(sql, params or ())
        conn.commit()
        return cur.lastrowid

# ------------------ PAGE LAYOUT ------------------
st.set_page_config(page_title="Immigration Integration Dashboard", layout="wide")
st.title("🧭 Immigration Integration Dashboard")
st.caption("CRUD for two entities + 5 analytical queries (parameterized).")

tabs = st.tabs([
    "🏘️ Communities (CRUD)",
    "🏥 Service Providers (CRUD)",
    "📊 Analytics"
])

# ================== TAB 1: COMMUNITIES ==================
with tabs[0]:
    st.subheader("Communities")

    # Create
    with st.expander("➕ Create"):
        with st.form("create_comm"):
            name = st.text_input("Name", placeholder="San Antonio – Westside")
            zip_code = st.text_input("ZIP (5)", max_chars=5)
            state_code = st.text_input("State (2)", max_chars=2).upper()
            population = st.number_input("Population", min_value=0, step=100)
            foreign_born_pct = st.number_input("Foreign-born %", min_value=0.0, max_value=100.0, step=0.1)
            rural = st.checkbox("Rural?")
            go = st.form_submit_button("Create")
        if go:
            run_exec(
                """INSERT INTO communities (name, zip_code, state_code, population, foreign_born_pct, rural_flag)
                   VALUES (%s,%s,%s,%s,%s,%s)""",
                (name, zip_code, state_code, int(population), float(foreign_born_pct), 1 if rural else 0),
            )
            st.success("Community created.")

    # Read
    with st.expander("🗂️ Read / Filter"):
        state_f = st.text_input("Filter by state (optional)").upper()
        q = "SELECT community_id, name, zip_code, state_code, population, foreign_born_pct, rural_flag, created_at FROM communities"
        params = []
        if state_f:
            q += " WHERE state_code=%s"
            params.append(state_f)
        q += " ORDER BY state_code, zip_code"
        st.dataframe(run_select(q, params), use_container_width=True)

    # Update
    with st.expander("✏️ Update"):
        df_ids = run_select("SELECT community_id, name, zip_code FROM communities ORDER BY community_id")
        if df_ids.empty:
            st.info("No communities yet.")
        else:
            pick = st.selectbox(
                "Select",
                df_ids.apply(lambda r: f"{r.community_id} – {r.name} ({r.zip_code})", axis=1)
            )
            comm_id = int(pick.split(" – ")[0])
            row = run_select("SELECT * FROM communities WHERE community_id=%s", (comm_id,)).iloc[0]
            name_u = st.text_input("Name", row["name"])
            pop_u = st.number_input("Population", 0, value=int(row["population"] or 0), step=100)
            fb_u = st.number_input("Foreign-born %", 0.0, 100.0, float(row["foreign_born_pct"] or 0.0), 0.1)
            rural_u = st.checkbox("Rural?", bool(row["rural_flag"]))
            if st.button("Save Changes"):
                run_exec(
                    """UPDATE communities
                       SET name=%s, population=%s, foreign_born_pct=%s, rural_flag=%s
                       WHERE community_id=%s""",
                    (name_u, int(pop_u), float(fb_u), 1 if rural_u else 0, comm_id)
                )
                st.success("Updated.")

    # Delete
    with st.expander("🗑️ Delete"):
        df_ids = run_select("SELECT community_id, name FROM communities ORDER BY community_id")
        if df_ids.empty:
            st.info("No communities to delete.")
        else:
            pick = st.selectbox("Select", df_ids.apply(lambda r: f"{r.community_id} – {r.name}", axis=1))
            comm_id = int(pick.split(" – ")[0])
            if st.button("Delete Community"):
                try:
                    run_exec("DELETE FROM communities WHERE community_id=%s", (comm_id,))
                    st.success("Deleted.")
                except Exception as e:
                    st.error(f"Delete failed (FK constraints?): {e}")

# ================== TAB 2: PROVIDERS ==================
with tabs[1]:
    st.subheader("Service Providers")

    # Create
    with st.expander("➕ Create"):
        df_comm = run_select("SELECT community_id, name, zip_code FROM communities ORDER BY name")
        if df_comm.empty:
            st.warning("Create a community first.")
        else:
            with st.form("create_provider"):
                name = st.text_input("Provider name", placeholder="Westside Legal Aid")
                ptype = st.text_input("Provider type", placeholder="legal_aid / ESL / workforce / health_nav")
                comm_label = st.selectbox(
                    "Community",
                    df_comm.apply(lambda r: f"{r.community_id} – {r.name} ({r.zip_code})", axis=1)
                )
                comm_id = int(comm_label.split(" – ")[0])
                zip_code = st.text_input("ZIP", max_chars=5)
                capacity = st.number_input("Capacity / week", min_value=0, step=5)
                pro_bono = st.checkbox("Accepts pro bono?")
                go = st.form_submit_button("Create")
            if go:
                run_exec(
                    """INSERT INTO service_providers
                       (name, provider_type, community_id, zip_code, capacity_per_week, accepts_pro_bono)
                       VALUES (%s,%s,%s,%s,%s,%s)""",
                    (name, ptype, comm_id, zip_code, int(capacity), 1 if pro_bono else 0)
                )
                st.success("Provider created.")

    # Read
    with st.expander("🗂️ Read / Filter"):
        pfilter = st.text_input("Filter by provider_type (optional)")
        q = """SELECT p.provider_id, p.name, p.provider_type, p.zip_code,
                      p.capacity_per_week, p.accepts_pro_bono,
                      c.name AS community_name, c.state_code
               FROM service_providers p
               JOIN communities c ON c.community_id=p.community_id"""
        params = []
        if pfilter:
            q += " WHERE p.provider_type=%s"
            params.append(pfilter)
        q += " ORDER BY c.state_code, p.name"
        st.dataframe(run_select(q, params), use_container_width=True)

    # Update
    with st.expander("✏️ Update"):
        df_ids = run_select("SELECT provider_id, name FROM service_providers ORDER BY provider_id")
        if df_ids.empty:
            st.info("No providers yet.")
        else:
            pick = st.selectbox("Select", df_ids.apply(lambda r: f"{r.provider_id} – {r.name}", axis=1))
            pid = int(pick.split(" – ")[0])
            row = run_select("SELECT * FROM service_providers WHERE provider_id=%s", (pid,)).iloc[0]
            name_u = st.text_input("Name", row["name"])
            ptype_u = st.text_input("Provider type", row["provider_type"])
            cap_u = st.number_input("Capacity / week", 0, value=int(row["capacity_per_week"] or 0), step=5)
            pro_u = st.checkbox("Accepts pro bono?", bool(row["accepts_pro_bono"]))
            if st.button("Save Provider Changes"):
                run_exec(
                    """UPDATE service_providers
                       SET name=%s, provider_type=%s, capacity_per_week=%s, accepts_pro_bono=%s
                       WHERE provider_id=%s""",
                    (name_u, ptype_u, int(cap_u), 1 if pro_u else 0, pid)
                )
                st.success("Updated.")

    # Delete
    with st.expander("🗑️ Delete"):
        df_ids = run_select("SELECT provider_id, name FROM service_providers ORDER BY provider_id")
        if df_ids.empty:
            st.info("No providers to delete.")
        else:
            pick = st.selectbox("Select", df_ids.apply(lambda r: f"{r.provider_id} – {r.name}", axis=1))
            pid = int(pick.split(" – ")[0])
            if st.button("Delete Provider"):
                try:
                    run_exec("DELETE FROM service_providers WHERE provider_id=%s", (pid,))
                    st.success("Deleted.")
                except Exception as e:
                    st.error(f"Delete failed (FK constraints?): {e}")

# ================== TAB 3: ANALYTICS (5 QUERIES) ==================
with tabs[2]:
    st.subheader("Back-End Analytical Queries")

    c1, c2 = st.columns(2, gap="large")

    # Q1
    with c1:
        st.markdown("**Q1. Capacity per 1,000 residents below threshold**")
        threshold = st.number_input("Threshold (capacity per 1,000)", 0.0, 999.0, 0.5, 0.1)
        q1 = """
        SELECT c.zip_code, c.population,
               COALESCE(SUM(p.capacity_per_week),0) AS weekly_capacity,
               ROUND((COALESCE(SUM(p.capacity_per_week),0) / NULLIF(c.population,0)) * 1000, 3) AS capacity_per_1000
        FROM communities c
        LEFT JOIN service_providers p ON p.community_id = c.community_id
        GROUP BY c.zip_code, c.population
        HAVING capacity_per_1000 < %s
        ORDER BY capacity_per_1000 ASC;
        """
        st.dataframe(run_select(q1, (threshold,)), use_container_width=True)

    # Q2
    with c2:
        st.markdown("**Q2. Attendance vs no_car_pct (ACS year)**")
        year = st.number_input("ACS Year", 2005, 2100, 2024, 1)
        q2 = """
        SELECT c.zip_code,
               ROUND(AVG(CASE WHEN a.attended_flag=1 THEN 1 ELSE 0 END),3) AS attendance_rate,
               d.no_car_pct
        FROM intake_cases ic
        JOIN appointments a ON a.case_id = ic.case_id
        JOIN communities c ON c.community_id = ic.community_id
        JOIN demographics d ON d.zip_code = c.zip_code AND d.year = %s
        GROUP BY c.zip_code, d.no_car_pct
        ORDER BY attendance_rate ASC;
        """
        st.dataframe(run_select(q2, (int(year),)), use_container_width=True)

    # Q3
    with c1:
        st.markdown("**Q3. Median closed-case duration (days) by case_type**")
        q3 = """
        SELECT case_type,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DATEDIFF(date_closed, date_opened)) AS median_days
        FROM intake_cases
        WHERE date_closed IS NOT NULL
        GROUP BY case_type
        ORDER BY median_days DESC;
        """
        try:
            st.dataframe(run_select(q3), use_container_width=True)
        except Exception:
            q3b = """
            WITH durations AS (
              SELECT case_type, DATEDIFF(date_closed, date_opened) AS dd
              FROM intake_cases
              WHERE date_closed IS NOT NULL
            ),
            ranked AS (
              SELECT case_type, dd,
                     ROW_NUMBER() OVER (PARTITION BY case_type ORDER BY dd) AS rn,
                     COUNT(*) OVER (PARTITION BY case_type) AS cnt
              FROM durations
            )
            SELECT case_type, AVG(dd) AS median_days
            FROM ranked
            WHERE rn IN (FLOOR((cnt+1)/2), CEIL((cnt+1)/2))
            GROUP BY case_type
            ORDER BY median_days DESC;
            """
            st.dataframe(run_select(q3b), use_container_width=True)

    # Q4
    with c2:
        st.markdown("**Q4. Open cases older than N days**")
        min_days = st.number_input("Min days open", 1, 10000, 30, 5)
        q4 = """
        SELECT ic.case_id, ic.case_type, sp.name AS provider_name, c.zip_code,
               DATEDIFF(CURDATE(), ic.date_opened) AS days_open
        FROM intake_cases ic
        JOIN service_providers sp ON sp.provider_id = ic.provider_id
        JOIN communities c ON c.community_id = ic.community_id
        WHERE ic.status='open' AND DATEDIFF(CURDATE(), ic.date_opened) >= %s
        ORDER BY days_open DESC;
        """
        st.dataframe(run_select(q4, (int(min_days),)), use_container_width=True)

    # Q5
    st.markdown("**Q5. USCIS quarterly totals by case_type**")
    fy = st.number_input("Fiscal Year", 2005, 2100, 2025, 1)
    qtr = st.selectbox("Quarter", [1, 2, 3, 4], index=2)
    q5 = """
    SELECT case_type, receipts, approvals, denials, pending_begin, pending_end, completed
    FROM case_stats_quarterly
    WHERE fiscal_year=%s AND quarter_num=%s
    ORDER BY case_type;
    """
    st.dataframe(run_select(q5, (int(fy), int(qtr))), use_container_width=True)
