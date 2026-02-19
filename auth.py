#!/usr/bin/env python3
"""
用户认证模块 - 基于 Supabase
处理登录、注册、登出
"""

import streamlit as st
from supabase import create_client


def get_supabase():
    """获取 Supabase 客户端"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def login(email: str, password: str):
    """
    用户登录
    返回 (user, error_message)
    成功时 error_message 为 None，失败时 user 为 None
    """
    try:
        sb = get_supabase()
        res = sb.auth.sign_in_with_password({"email": email, "password": password})
        return res.user, None
    except Exception as e:
        msg = str(e)
        if "Invalid login credentials" in msg:
            return None, "邮箱或密码错误，请重试"
        if "Email not confirmed" in msg:
            return None, "请先前往邮箱点击验证链接，再登录"
        return None, f"登录失败：{msg}"


def register(email: str, password: str):
    """
    用户注册
    返回 (user, error_message)
    """
    try:
        sb = get_supabase()
        res = sb.auth.sign_up({"email": email, "password": password})
        return res.user, None
    except Exception as e:
        msg = str(e)
        if "User already registered" in msg:
            return None, "该邮箱已注册，请直接登录"
        if "Password should be" in msg:
            return None, "密码至少需要6位字符"
        return None, f"注册失败：{msg}"


def logout():
    """退出登录，清除所有会话状态"""
    try:
        sb = get_supabase()
        sb.auth.sign_out()
    except Exception:
        pass
    # 清除 session state
    for key in ["logged_in", "user_email", "user_id"]:
        st.session_state.pop(key, None)


def is_logged_in() -> bool:
    """检查当前是否已登录"""
    return st.session_state.get("logged_in", False)


def get_current_user_email() -> str:
    """获取当前登录用户的邮箱"""
    return st.session_state.get("user_email", "")


def set_session(user):
    """将登录用户信息写入 session state"""
    st.session_state["logged_in"] = True
    st.session_state["user_email"] = user.email
    st.session_state["user_id"] = user.id
