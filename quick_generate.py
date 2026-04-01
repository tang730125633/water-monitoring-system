#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速生成测试数据到数据库
"""

import sqlite3
import time
import random
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_TMP_DB = "/tmp/water.db"
_LOCAL_DB = os.path.join(_SCRIPT_DIR, "water.db")

if os.path.exists(_TMP_DB):
    DB_PATH = _TMP_DB
elif os.access(_SCRIPT_DIR, os.W_OK):
    DB_PATH = _LOCAL_DB
else:
    DB_PATH = _TMP_DB

# 城市配置 - 必须和 app_streamlit.py 中的 CITY_DEVICE_MAP 完全对应
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
    "成都市": {
        "device_id": "water_sensor_chengdu",
        "data_ranges": {
            "ph": (7.0, 8.0),
            "do": (5.5, 9.5),
            "turb": (1.0, 4.5),
            "temp": (10.0, 28.0),
            "ec": (200.0, 900.0),
        }
    },
    "武汉市": {
        "device_id": "water_sensor_wuhan",
        "data_ranges": {
            "ph": (6.8, 7.8),
            "do": (5.0, 10.0),
            "turb": (1.2, 4.0),
            "temp": (8.0, 32.0),
            "ec": (180.0, 850.0),
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
    "杭州市": {
        "device_id": "water_sensor_hangzhou",
        "data_ranges": {
            "ph": (6.8, 7.6),
            "do": (6.0, 11.0),
            "turb": (0.6, 3.0),
            "temp": (10.0, 33.0),
            "ec": (150.0, 750.0),
        }
    },
    "南京市": {
        "device_id": "water_sensor_nanjing",
        "data_ranges": {
            "ph": (7.0, 8.0),
            "do": (5.5, 10.5),
            "turb": (1.0, 3.5),
            "temp": (6.0, 31.0),
            "ec": (200.0, 950.0),
        }
    },
    "重庆市": {
        "device_id": "water_sensor_chongqing",
        "data_ranges": {
            "ph": (7.0, 8.2),
            "do": (5.0, 9.5),
            "turb": (1.5, 5.5),
            "temp": (12.0, 34.0),
            "ec": (180.0, 800.0),
        }
    },
    "巢湖市": {
        "device_id": "water_sensor_chaohu",
        "data_ranges": {
            "ph": (6.8, 8.0),
            "do": (5.0, 10.5),
            "turb": (2.0, 7.0),
            "temp": (8.0, 32.0),
            "ec": (250.0, 900.0),
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


def generate_city_data(city_name, city_config, hours=24, interval=30):
    """为指定城市生成数据"""
    device_id = city_config["device_id"]
    ranges = city_config["data_ranges"]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    end_time = int(time.time())
    start_time = end_time - hours * 3600

    # 获取该设备当前最大 seq
    row = cursor.execute(
        "SELECT MAX(seq) FROM metric WHERE device_id = ?", (device_id,)
    ).fetchone()
    seq = (row[0] or 0) + 1

    count = 0
    current_time = start_time

    while current_time <= end_time:
        ph = round(random.uniform(*ranges["ph"]), 2)
        do_val = round(random.uniform(*ranges["do"]), 2)
        turb = round(random.uniform(*ranges["turb"]), 2)
        temp = round(random.uniform(*ranges["temp"]), 2)
        ec = round(random.uniform(*ranges["ec"]), 2)
        alarm = 1 if random.random() < 0.1 else 0

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
            count += 1
        except sqlite3.IntegrityError:
            seq += 1

        current_time += interval

    conn.commit()
    conn.close()
    print(f"[OK] Generated {count} records for {city_name}")


def regenerate_all(hours=24, interval=30):
    """清空旧数据，为所有城市重新生成"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM metric")
    conn.commit()
    conn.close()
    create_database()
    for city_name, config in CITY_CONFIG.items():
        generate_city_data(city_name, config, hours=hours, interval=interval)


def main():
    print("=" * 60)
    print(" Water Monitoring System - Test Data Generator")
    print("=" * 60)
    print()
    print("Creating database...")
    create_database()
    print()
    print("Generating test data for all cities...")
    regenerate_all()
    print()
    print("=" * 60)
    print("[OK] All data generated successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
