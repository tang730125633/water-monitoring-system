#!/usr/bin/env python3
"""
水环境监测数据可视化仪表盘
使用Streamlit展示实时数据曲线和告警信息
"""

import sqlite3
import pandas as pd
import time
import os
import streamlit as st
import plotly.graph_objects as go
import quick_generate

# 页面配置
st.set_page_config(
    page_title="水环境监测系统",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据库配置 - 使用脚本所在目录的绝对路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "water.db")

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
    "巢湖市": "water_sensor_chaohu",
}


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
    """主仪表盘"""

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

def ensure_fresh_data():
    """检查数据是否过期，过期则重新生成（每次启动只跑一次）"""
    if st.session_state.get("data_initialized"):
        return
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        row = conn.execute(
            "SELECT MAX(ts) FROM metric"
        ).fetchone()
        conn.close()
        latest_ts = row[0] if row and row[0] else 0
        # 数据超过2小时没更新，则清空重新生成
        if int(time.time()) - latest_ts > 7200:
            conn2 = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn2.execute("DELETE FROM metric")
            conn2.commit()
            conn2.close()
            for city_name, config in quick_generate.CITY_CONFIG.items():
                quick_generate.generate_city_data(city_name, config, hours=24, interval=30)
    except Exception:
        # 数据库/表不存在时，初始化并全量生成
        quick_generate.create_database()
        for city_name, config in quick_generate.CITY_CONFIG.items():
            quick_generate.generate_city_data(city_name, config, hours=24, interval=30)
    st.session_state["data_initialized"] = True


def main():
    ensure_fresh_data()
    show_dashboard()


if __name__ == "__main__":
    main()
