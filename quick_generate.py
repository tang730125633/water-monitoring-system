#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速生成测试数据到数据库（Windows兼容版本）
"""

import sqlite3
import time
import random
from datetime import datetime, timedelta

DB_PATH = "water.db"

# 城市配置
CITY_CONFIG = {
    "北京市": {
        "device_id": "water_sensor_beijing",
        "data_ranges": {
            "ph": (7.2, 8.2),
            "do": (6.0, 10.0),
            "turb": (1.0, 4.0),
            "temp": (5.0, 25.0),
            "ec": (300.0, 1200.0),
        }
    },
    "上海市": {
        "device_id": "water_sensor_shanghai",
        "data_ranges": {
            "ph": (6.8, 7.8),
            "do": (5.5, 11.0),
            "turb": (0.8, 3.5),
            "temp": (12.0, 32.0),
            "ec": (200.0, 1000.0),
        }
    },
    "广州市": {
        "device_id": "water_sensor_guangzhou",
        "data_ranges": {
            "ph": (6.5, 7.5),
            "do": (5.0, 10.0),
            "turb": (1.5, 5.0),
            "temp": (18.0, 35.0),
            "ec": (150.0, 800.0),
        }
    },
    "深圳市": {
        "device_id": "water_sensor_shenzhen",
        "data_ranges": {
            "ph": (7.0, 8.0),
            "do": (6.5, 12.0),
            "turb": (0.5, 2.5),
            "temp": (20.0, 33.0),
            "ec": (100.0, 600.0),
        }
    },
    "西安市": {
        "device_id": "water_sensor_xian",
        "data_ranges": {
            "ph": (7.5, 8.5),
            "do": (5.5, 10.0),
            "turb": (0.8, 3.0),
            "temp": (5.0, 30.0),
            "ec": (400.0, 1500.0),
        }
    },
}


def create_database():
    """创建数据库表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metric (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            ts INTEGER NOT NULL,
            seq INTEGER NOT NULL,
            ph REAL,
            do REAL,
            turb REAL,
            temp REAL,
            ec REAL,
            alarm INTEGER DEFAULT 0,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            UNIQUE(device_id, seq)
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_metric_device_ts ON metric(device_id, ts)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_metric_alarm ON metric(alarm)"
    )
    conn.commit()
    conn.close()
    print("[OK] Database created successfully")


def generate_city_data(city_name, city_config, hours=24, interval=30):
    """为指定城市生成数据"""
    device_id = city_config["device_id"]
    ranges = city_config["data_ranges"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 计算时间范围
    end_time = int(time.time())
    start_time = end_time - hours * 3600

    seq = 0
    current_time = start_time

    while current_time <= end_time:
        # 生成随机数据
        ph = round(random.uniform(*ranges["ph"]), 2)
        do_val = round(random.uniform(*ranges["do"]), 2)
        turb = round(random.uniform(*ranges["turb"]), 2)
        temp = round(random.uniform(*ranges["temp"]), 2)
        ec = round(random.uniform(*ranges["ec"]), 2)

        # 10%概率产生告警
        alarm = 1 if random.random() < 0.1 else 0

        # 插入数据
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO metric
                (device_id, ts, seq, ph, do, turb, temp, ec, alarm)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (device_id, current_time, seq, ph, do_val, turb, temp, ec, alarm)
            )
            seq += 1
        except sqlite3.IntegrityError:
            pass

        current_time += interval

    conn.commit()
    conn.close()
    print(f"[OK] Generated {seq} records for {city_name}")


def main():
    print("=" * 60)
    print(" Water Monitoring System - Test Data Generator")
    print("=" * 60)
    print()

    # 1. 创建数据库
    print("Step 1: Creating database...")
    create_database()
    print()

    # 2. 生成各城市数据
    print("Step 2: Generating test data...")
    for city_name, config in CITY_CONFIG.items():
        generate_city_data(city_name, config, hours=24, interval=30)

    print()
    print("=" * 60)
    print("[OK] All data generated successfully!")
    print("=" * 60)
    print()
    print("You can now run: streamlit run app_streamlit.py")
    print()


if __name__ == "__main__":
    main()
