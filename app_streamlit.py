#!/usr/bin/env python3
"""
水环境监测数据可视化仪表盘
使用Streamlit展示实时数据曲线和告警信息
支持用户登录/注册（Supabase云端认证）
"""

import sqlite3
import pandas as pd
import time
import streamlit as st
import plotly.graph_objects as go
import auth

# 页面配置
st.set_page_config(
    page_title="水环境监测系统",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据库配置
DB_PATH = "water.db"

# 城市到设备的映射
CITY_DEVICE_MAP = {
    "北京市": "water_sensor_beijing",
    "上海市": "water_sensor_shanghai",
    "广州市": "water_sensor_guangzhou",
    "深圳市": "water_sensor_shenzhen",
    "成都市": "water_sensor_chengdu",
    "武汉市": "water_sensor_wuhan",
    "西安市": "water_sensor_xian",
    "杭州市": "water_sensor_hangzhou",
    "南京市": "water_sensor_nanjing",
    "重庆市": "water_sensor_chongqing",
}


# ─────────────────────────────────────────────
# 登录 / 注册 页面
# ─────────────────────────────────────────────

def show_auth_page():
    """未登录时展示的登录/注册界面"""

    # 自定义样式
    st.markdown("""
    <style>
    /* 隐藏默认顶栏 deploy 按钮等 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* 登录卡片居中 */
    .auth-card {
        max-width: 440px;
        margin: 60px auto 0 auto;
        padding: 40px 36px;
        background: #ffffff;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(26,82,118,0.12);
        border: 1px solid #D6EAF8;
    }
    .auth-title {
        text-align: center;
        color: #1A5276;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .auth-subtitle {
        text-align: center;
        color: #5D6D7E;
        font-size: 0.9rem;
        margin-bottom: 28px;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── 居中 Logo & 标题 ──
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown('<div class="auth-title">💧 水环境监测系统</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-subtitle">Water Environment Monitoring System</div>', unsafe_allow_html=True)
        st.markdown("---")

        # ── 登录 / 注册 两个标签页 ──
        tab_login, tab_register = st.tabs(["🔑 登录", "📝 注册账号"])

        # ── 登录 Tab ──
        with tab_login:
            st.markdown("#### 欢迎回来")
            with st.form("login_form", clear_on_submit=False):
                email = st.text_input("邮箱", placeholder="your@email.com")
                password = st.text_input("密码", type="password", placeholder="请输入密码")
                submitted = st.form_submit_button("登 录", use_container_width=True, type="primary")

            if submitted:
                if not email or not password:
                    st.error("请填写邮箱和密码")
                else:
                    with st.spinner("登录中..."):
                        user, err = auth.login(email.strip(), password)
                    if err:
                        st.error(f"❌ {err}")
                    else:
                        auth.set_session(user)
                        st.success("✅ 登录成功！")
                        time.sleep(0.8)
                        st.rerun()

        # ── 注册 Tab ──
        with tab_register:
            st.markdown("#### 创建新账号")
            with st.form("register_form", clear_on_submit=True):
                reg_email = st.text_input("邮箱", placeholder="your@email.com", key="reg_email")
                reg_pwd = st.text_input("密码（至少6位）", type="password", placeholder="请设置密码", key="reg_pwd")
                reg_pwd2 = st.text_input("确认密码", type="password", placeholder="再输入一次密码", key="reg_pwd2")
                reg_submitted = st.form_submit_button("注 册", use_container_width=True, type="primary")

            if reg_submitted:
                if not reg_email or not reg_pwd:
                    st.error("请填写完整信息")
                elif reg_pwd != reg_pwd2:
                    st.error("❌ 两次密码不一致，请重新输入")
                elif len(reg_pwd) < 6:
                    st.error("❌ 密码至少需要6位字符")
                else:
                    with st.spinner("注册中..."):
                        user, err = auth.register(reg_email.strip(), reg_pwd)
                    if err:
                        st.error(f"❌ {err}")
                    else:
                        # Supabase 默认需要邮箱验证
                        # 如果你在 Supabase 关闭了邮箱验证，user 会直接返回已激活账号
                        if user and user.email:
                            st.success("✅ 注册成功！请切换到「登录」标签页登录。")
                            st.info("💡 提示：如果无法登录，请检查邮箱是否收到验证邮件并点击确认。")
                        else:
                            st.warning("注册请求已发送，请查收验证邮件后再登录。")


# ─────────────────────────────────────────────
# 主仪表盘数据函数
# ─────────────────────────────────────────────

@st.cache_data(ttl=30)
def load_data(device_id, hours=24):
    """加载指定设备的数据"""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        since = int(time.time()) - hours * 3600
        query = """
        SELECT ts, ph, do, turb, temp, ec, alarm, created_at
        FROM metric
        WHERE device_id = ? AND ts >= ?
        ORDER BY ts
        """
        df = pd.read_sql_query(query, conn, params=(device_id, since))
        conn.close()
        if not df.empty:
            df["datetime"] = pd.to_datetime(df["ts"], unit="s")
            df["created_datetime"] = pd.to_datetime(df["created_at"], unit="s")
            df["time_str"] = df["datetime"].dt.strftime("%H:%M:%S")
        return df
    except Exception as e:
        st.error(f"数据加载错误: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=60)
def get_devices():
    """获取所有设备列表"""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        devices = pd.read_sql_query(
            "SELECT DISTINCT device_id FROM metric ORDER BY device_id", conn
        )
        conn.close()
        return devices["device_id"].tolist() if not devices.empty else ["unknown"]
    except Exception:
        return ["unknown"]


@st.cache_data(ttl=60)
def get_alarm_data(device_id, hours=24):
    """获取告警数据"""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        since = int(time.time()) - hours * 3600
        query = """
        SELECT ts, ph, do, turb, temp, ec, alarm, created_at
        FROM metric
        WHERE device_id = ? AND ts >= ? AND alarm = 1
        ORDER BY ts DESC
        LIMIT 100
        """
        df = pd.read_sql_query(query, conn, params=(device_id, since))
        conn.close()
        if not df.empty:
            df["datetime"] = pd.to_datetime(df["ts"], unit="s")
            df["time_str"] = df["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
        return df
    except Exception as e:
        st.error(f"告警数据加载错误: {e}")
        return pd.DataFrame()


def create_line_chart(df, selected_metrics):
    """创建折线图"""
    if df.empty or not selected_metrics:
        return None
    fig = go.Figure()
    colors = {
        "ph": "#FF6B6B",
        "do": "#4ECDC4",
        "turb": "#45B7D1",
        "temp": "#FFA07A",
        "ec": "#98D8C8",
    }
    units = {
        "ph": "pH",
        "do": "mg/L",
        "turb": "NTU",
        "temp": "°C",
        "ec": "µS/cm",
    }
    for metric in selected_metrics:
        if metric in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["datetime"],
                    y=df[metric],
                    mode="lines+markers",
                    name=f"{metric.upper()} ({units.get(metric, '')})",
                    line=dict(color=colors.get(metric, "#000000"), width=2),
                    marker=dict(size=4),
                    hovertemplate=(
                        f"<b>{metric.upper()}</b><br>"
                        "时间: %{x}<br>"
                        f"值: %{{y:.2f}} {units.get(metric, '')}<br>"
                        "<extra></extra>"
                    ),
                )
            )
    fig.update_layout(
        title="水质参数趋势图",
        xaxis_title="时间",
        yaxis_title="数值",
        hovermode="x unified",
        showlegend=True,
        height=500,
        template="plotly_white",
    )
    return fig


def create_gauge_chart(value, title, min_val, max_val, color):
    """创建仪表盘图表"""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": title},
            delta={"reference": (min_val + max_val) / 2},
            gauge={
                "axis": {"range": [min_val, max_val]},
                "bar": {"color": color},
                "steps": [
                    {"range": [min_val, (min_val + max_val) * 0.3], "color": "lightgray"},
                    {"range": [(min_val + max_val) * 0.3, (min_val + max_val) * 0.7], "color": "gray"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": max_val * 0.9,
                },
            },
        )
    )
    fig.update_layout(height=200)
    return fig


# ─────────────────────────────────────────────
# 主仪表盘
# ─────────────────────────────────────────────

def show_dashboard():
    """已登录后展示的主仪表盘"""

    # 侧边栏 - 用户信息 & 退出
    st.sidebar.markdown("---")
    user_email = auth.get_current_user_email()
    st.sidebar.markdown(f"👤 **{user_email}**")
    if st.sidebar.button("退出登录", use_container_width=True):
        auth.logout()
        st.rerun()
    st.sidebar.markdown("---")

    # 城市选择
    st.sidebar.header("📍 地区选择")
    city = st.sidebar.selectbox(
        "选择城市",
        list(CITY_DEVICE_MAP.keys()),
        index=0,
        help="选择要查看的城市水环境数据"
    )
    device_id = CITY_DEVICE_MAP[city]

    st.title(f"💧 水环境监测系统 - {city}")
    st.caption(f"监测设备ID: {device_id}")
    st.markdown("---")

    st.sidebar.info(f"📡 监测设备: {device_id}")
    st.sidebar.markdown("---")

    with st.sidebar.expander("⚙️ 高级选项"):
        hours = st.slider("时间范围 (小时)", 1, 72, 24)
        st.markdown("**显示指标**")
        all_metrics = ["ph", "do", "turb", "temp", "ec"]
        selected_metrics = st.multiselect(
            "选择要显示的指标",
            all_metrics,
            default=["ph", "do", "temp"],
        )

    # 加载数据
    df = load_data(device_id, hours)
    if df.empty:
        st.warning("暂无数据，请检查设备连接或数据库")
        return

    # 顶部数据卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("pH值", f"{df['ph'].iloc[-1]:.2f}")
    with col2:
        st.metric("溶解氧", f"{df['do'].iloc[-1]:.2f} mg/L")
    with col3:
        st.metric("温度", f"{df['temp'].iloc[-1]:.2f} °C")
    with col4:
        st.metric("告警次数", int(df["alarm"].sum()))

    st.markdown("---")

    # 趋势图
    st.subheader("📈 数据趋势")
    fig = create_line_chart(df, selected_metrics)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    # 仪表盘
    if not df.empty:
        st.subheader("📊 实时仪表盘")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.plotly_chart(create_gauge_chart(df["ph"].iloc[-1], "pH值", 0, 14, "blue"), use_container_width=True)
        with col2:
            st.plotly_chart(create_gauge_chart(df["do"].iloc[-1], "溶解氧", 0, 20, "green"), use_container_width=True)
        with col3:
            st.plotly_chart(create_gauge_chart(df["temp"].iloc[-1], "温度", 0, 50, "orange"), use_container_width=True)

    # 告警信息
    st.subheader("🚨 告警信息")
    alarm_df = get_alarm_data(device_id, hours)
    if not alarm_df.empty:
        st.dataframe(
            alarm_df[["time_str", "ph", "do", "turb", "temp", "ec"]].head(20),
            use_container_width=True,
            column_config={
                "time_str": "时间",
                "ph": "pH值",
                "do": "溶解氧",
                "turb": "浊度",
                "temp": "温度",
                "ec": "电导率",
            },
        )
    else:
        st.info("当前时间段内无告警记录")

    # 数据统计
    st.subheader("📋 数据统计")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**数据概览**")
        st.write(f"- 数据点数: {len(df)}")
        st.write(
            f"- 时间范围: {df['datetime'].min().strftime('%H:%M')} - "
            f"{df['datetime'].max().strftime('%H:%M')}"
        )
        st.write(f"- 告警次数: {int(df['alarm'].sum())}")
    with col2:
        st.write("**数值范围**")
        for metric in selected_metrics:
            if metric in df.columns:
                st.write(
                    f"- {metric.upper()}: "
                    f"{df[metric].min():.2f} ~ {df[metric].max():.2f} (平均: {df[metric].mean():.2f})"
                )

    # 自动刷新
    if st.sidebar.checkbox("自动刷新", value=True):
        time.sleep(5)
        st.rerun()


# ─────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────

def main():
    if not auth.is_logged_in():
        show_auth_page()
    else:
        show_dashboard()


if __name__ == "__main__":
    main()
