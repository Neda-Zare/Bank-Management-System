"""
Bank Management System - CLI
=============================
Refactored client for the bank_schema.sql database.

Design notes:
- Every DB call goes through call_function()/call_procedure() so error
  handling and commit/rollback happen in exactly one place.
- Passwords are hashed with bcrypt on the client before ever reaching
  the database (see hash_password / verify_password). The database
  never sees a plain-text password.
- Input for numbers/dates is validated in a loop instead of trusting
  the user, so a bad value re-prompts instead of crashing the program.
"""

import sys
import getpass
from datetime import datetime, date
from decimal import Decimal, InvalidOperation

import psycopg2
import bcrypt


# =====================================================================
# DATABASE CONNECTION
# =====================================================================

import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "sslmode": "require",
}


def get_connection():
    """Open a fresh connection. Raises if the DB is unreachable."""
    return psycopg2.connect(**DB_CONFIG)


def call_function(conn, sql, params=()):
    """
    Run a SELECT-style call to a DB function and return all rows.
    Commits on success, rolls back on failure, always re-raises so the
    caller's menu can show a clean error message.
    """
    with conn.cursor() as cur:
        try:
            cur.execute(sql, params)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            conn.commit()
            return columns, rows
        except Exception:
            conn.rollback()
            raise


def call_procedure(conn, sql, params=()):
    """Run a CALL to a stored procedure (no result rows expected)."""
    with conn.cursor() as cur:
        try:
            cur.execute(sql, params)
            conn.commit()
        except Exception:
            conn.rollback()
            raise


# =====================================================================
# PASSWORD HASHING
# =====================================================================

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())


# =====================================================================
# INPUT HELPERS (validate, re-prompt on bad input instead of crashing)
# =====================================================================

def input_text(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("این فیلد نمی‌تواند خالی باشد.")


def input_password(prompt: str) -> str:
    while True:
        value = getpass.getpass(prompt)
        if value:
            return value
        print("پسورد نمی‌تواند خالی باشد.")


def input_decimal(prompt: str) -> Decimal:
    while True:
        raw = input(prompt).strip()
        try:
            value = Decimal(raw)
            if value < 0:
                print("مقدار نمی‌تواند منفی باشد.")
                continue
            return value
        except InvalidOperation:
            print("لطفاً یک عدد معتبر وارد کنید.")


def input_date(prompt: str) -> date:
    while True:
        raw = input(f"{prompt} (YYYY-MM-DD): ").strip()
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("فرمت تاریخ نامعتبر است. مثال: 2026-08-17")


def input_yes_no(prompt: str) -> bool:
    while True:
        raw = input(f"{prompt} (y/n): ").strip().lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        print("لطفاً y یا n وارد کنید.")


def print_table(columns, rows):
    if not rows:
        print("(نتیجه‌ای یافت نشد)")
        return
    widths = [max(len(str(c)), *(len(str(r[i])) for r in rows)) for i, c in enumerate(columns)]
    header = " | ".join(str(c).ljust(w) for c, w in zip(columns, widths))
    print(header)
    print("-" * len(header))
    for row in rows:
        print(" | ".join(str(v).ljust(w) for v, w in zip(row, widths)))


# =====================================================================
# AUTH
# =====================================================================

def register_user(conn):
    print("\n--- ثبت‌نام کاربر جدید ---")
    username = input_text("نام کاربری: ")
    password = input_password("رمز عبور: ")
    first_name = input_text("نام: ")
    last_name = input_text("نام خانوادگی: ")
    birth_date = input_date("تاریخ تولد")
    phone_number = input_text("شماره تلفن: ")

    try:
        call_function(
            conn,
            "SELECT create_user(%s, %s, %s, %s, %s, %s)",
            (username, hash_password(password), first_name, last_name, birth_date, phone_number),
        )
        print("ثبت‌نام با موفقیت انجام شد. حالا می‌توانید وارد شوید.")
    except psycopg2.Error as e:
        print(f"خطا در ثبت‌نام: {e.pgerror or e}")


def login(conn):
    print("\n--- ورود ---")
    username = input_text("نام کاربری: ")
    password = input_password("رمز عبور: ")

    try:
        _, rows = call_function(conn, "SELECT * FROM get_login_credentials(%s)", (username,))
    except psycopg2.Error as e:
        print(f"خطای دیتابیس: {e.pgerror or e}")
        return None

    if not rows or rows[0][0] is None:
        print("نام کاربری یافت نشد.")
        return None

    user_id, role, password_hash = rows[0]
    if not verify_password(password, password_hash):
        print("رمز عبور اشتباه است.")
        return None

    print(f"خوش آمدید! نقش شما: {role}")
    return {"user_id": user_id, "role": role, "username": username}


# =====================================================================
# USER MENU (customer-facing)
# =====================================================================

def menu_user(conn, session):
    user_id = session["user_id"]
    while True:
        print("\n=== منوی کاربر ===")
        print("1) مشاهده حساب‌های من")
        print("2) انجام تراکنش (واریز/برداشت)")
        print("3) درخواست وام")
        print("4) مشاهده وام‌های من")
        print("5) پرداخت قسط وام")
        print("0) خروج از حساب")
        choice = input("انتخاب: ").strip()

        try:
            if choice == "1":
                cols, rows = call_function(conn, "SELECT * FROM search_account_by_user_id(%s)", (user_id,))
                print_table(cols, rows)

            elif choice == "2":
                account_number = input_text("شماره حساب: ")
                t_type = input_text("نوع تراکنش (income/withdraw): ").lower()
                amount = input_decimal("مبلغ: ")
                call_function(conn, "SELECT make_transaction(%s, %s, %s)", (account_number, amount, t_type))
                print("تراکنش با موفقیت ثبت شد.")

            elif choice == "3":
                account_number = input_text("شماره حساب: ")
                amount = input_decimal("مبلغ وام درخواستی: ")
                request_date = input_date("تاریخ درخواست")
                cols, rows = call_function(
                    conn, "SELECT check_loan_approval(%s, %s, %s)", (request_date, account_number, amount)
                )
                approved = rows[0][0]
                print("درخواست وام تایید شد ✅" if approved else "درخواست وام رد شد ❌")

            elif choice == "4":
                account_number = input_text("شماره حساب: ")
                cols, rows = call_function(
                    conn, "SELECT * FROM loans WHERE account_number = %s", (account_number,)
                )
                print_table(cols, rows)

            elif choice == "5":
                loan_id = input_text("شناسه وام (loan id): ")
                amount = input_decimal("مبلغ قسط: ")
                call_procedure(conn, "CALL make_loan_payment(%s, %s)", (loan_id, amount))
                print("قسط با موفقیت پرداخت شد.")

            elif choice == "0":
                return
            else:
                print("گزینه نامعتبر است.")

        except psycopg2.Error as e:
            print(f"خطا: {e.pgerror or e}")


# =====================================================================
# EMPLOYEE MENU
# =====================================================================

def menu_manage_users(conn):
    while True:
        print("\n--- مدیریت کاربران ---")
        print("1) لیست همه کاربران")
        print("2) جستجو با شماره تلفن")
        print("3) جستجو با نام کاربری")
        print("4) ساخت کاربر جدید")
        print("5) ویرایش کاربر (username/password)")
        print("6) حذف کاربر")
        print("0) بازگشت")
        choice = input("انتخاب: ").strip()

        try:
            if choice == "1":
                cols, rows = call_function(conn, "SELECT * FROM read_users()")
                print_table(cols, rows)
            elif choice == "2":
                phone = input_text("شماره تلفن: ")
                cols, rows = call_function(conn, "SELECT * FROM search_users_by_phone_number(%s)", (phone,))
                print_table(cols, rows)
            elif choice == "3":
                uname = input_text("بخشی از نام کاربری: ")
                cols, rows = call_function(conn, "SELECT * FROM filter_users_by_username(%s)", (uname,))
                print_table(cols, rows)
            elif choice == "4":
                register_user(conn)
            elif choice == "5":
                uid = input_text("شناسه کاربر (user_id): ")
                uname = input_text("نام کاربری جدید: ")
                pw = input_password("رمز عبور جدید: ")
                call_function(conn, "SELECT update_user(%s, %s, %s)", (uid, uname, hash_password(pw)))
                print("کاربر با موفقیت به‌روزرسانی شد.")
            elif choice == "6":
                uid = input_text("شناسه کاربر (user_id): ")
                if input_yes_no(f"از حذف کاربر {uid} مطمئنید؟"):
                    call_function(conn, "SELECT delete_user(%s)", (uid,))
                    print("کاربر حذف شد.")
            elif choice == "0":
                return
            else:
                print("گزینه نامعتبر است.")
        except psycopg2.Error as e:
            print(f"خطا: {e.pgerror or e}")


def menu_manage_accounts(conn):
    while True:
        print("\n--- مدیریت حساب‌ها ---")
        print("1) لیست همه حساب‌ها")
        print("2) جستجو با شماره حساب")
        print("3) جستجو با شناسه کاربر")
        print("4) ساخت حساب جدید")
        print("5) ویرایش حساب (موجودی/نام)")
        print("6) حذف حساب")
        print("0) بازگشت")
        choice = input("انتخاب: ").strip()

        try:
            if choice == "1":
                cols, rows = call_function(conn, "SELECT * FROM read_accounts()")
                print_table(cols, rows)
            elif choice == "2":
                num = input_text("شماره حساب: ")
                cols, rows = call_function(conn, "SELECT * FROM search_account_by_account_number(%s)", (num,))
                print_table(cols, rows)
            elif choice == "3":
                uid = input_text("شناسه کاربر: ")
                cols, rows = call_function(conn, "SELECT * FROM search_account_by_user_id(%s)", (uid,))
                print_table(cols, rows)
            elif choice == "4":
                num = input_text("شماره حساب جدید: ")
                balance = input_decimal("موجودی اولیه: ")
                name = input_text("نام حساب: ")
                uid = input_text("شناسه کاربر مالک: ")
                call_function(conn, "SELECT create_account(%s, %s, %s, %s)", (num, balance, name, uid))
                print("حساب با موفقیت ساخته شد.")
            elif choice == "5":
                num = input_text("شماره حساب: ")
                balance = input_decimal("موجودی جدید: ")
                name = input_text("نام جدید حساب: ")
                call_function(conn, "SELECT update_account(%s, %s, %s)", (num, balance, name))
                print("حساب به‌روزرسانی شد.")
            elif choice == "6":
                num = input_text("شماره حساب: ")
                if input_yes_no(f"از حذف حساب {num} مطمئنید؟"):
                    call_function(conn, "SELECT delete_account(%s)", (num,))
                    print("حساب حذف شد.")
            elif choice == "0":
                return
            else:
                print("گزینه نامعتبر است.")
        except psycopg2.Error as e:
            print(f"خطا: {e.pgerror or e}")


def menu_manage_loans(conn):
    while True:
        print("\n--- مدیریت وام‌ها ---")
        print("1) لیست همه وام‌ها")
        print("2) ساخت وام دستی")
        print("3) ویرایش وام")
        print("4) حذف وام")
        print("0) بازگشت")
        choice = input("انتخاب: ").strip()

        try:
            if choice == "1":
                cols, rows = call_function(conn, "SELECT * FROM read_loans()")
                print_table(cols, rows)
            elif choice == "2":
                num = input_text("شماره حساب: ")
                paid = input_decimal("مبلغ پرداخت‌شده تاکنون: ")
                start = input_date("تاریخ شروع")
                due = input_date("تاریخ سررسید")
                total = input_decimal("مبلغ کل وام: ")
                ret = input_decimal("مبلغ بازپرداخت (با سود): ")
                call_function(
                    conn, "SELECT create_loan(%s, %s, %s, %s, %s, %s)", (num, paid, start, due, total, ret)
                )
                print("وام ساخته شد.")
            elif choice == "3":
                lid = input_text("شناسه وام: ")
                num = input_text("شماره حساب: ")
                paid = input_decimal("مبلغ پرداخت‌شده: ")
                start = input_date("تاریخ شروع")
                due = input_date("تاریخ سررسید")
                total = input_decimal("مبلغ کل: ")
                ret = input_decimal("مبلغ بازپرداخت: ")
                call_function(
                    conn,
                    "SELECT update_loan(%s, %s, %s, %s, %s, %s, %s)",
                    (lid, num, paid, start, due, total, ret),
                )
                print("وام به‌روزرسانی شد.")
            elif choice == "4":
                lid = input_text("شناسه وام: ")
                if input_yes_no(f"از حذف وام {lid} مطمئنید؟"):
                    call_function(conn, "SELECT delete_loan(%s)", (lid,))
                    print("وام حذف شد.")
            elif choice == "0":
                return
            else:
                print("گزینه نامعتبر است.")
        except psycopg2.Error as e:
            print(f"خطا: {e.pgerror or e}")


def menu_manage_loan_payments(conn):
    while True:
        print("\n--- مدیریت اقساط وام ---")
        print("1) لیست همه اقساط")
        print("2) مرتب‌سازی اقساط بر اساس تاریخ")
        print("3) ثبت قسط دستی")
        print("4) ویرایش قسط")
        print("5) حذف قسط")
        print("0) بازگشت")
        choice = input("انتخاب: ").strip()

        try:
            if choice == "1":
                cols, rows = call_function(conn, "SELECT * FROM read_loan_payments()")
                print_table(cols, rows)
            elif choice == "2":
                cols, rows = call_function(conn, "SELECT * FROM sort_loan_payments_by_date()")
                print_table(cols, rows)
            elif choice == "3":
                lid = input_text("شناسه وام: ")
                month = input_date("ماه پرداخت")
                amount = input_decimal("مبلغ قسط: ")
                call_function(conn, "SELECT create_loan_payment(%s, %s, %s)", (lid, month, amount))
                print("قسط ثبت شد.")
            elif choice == "4":
                pid = input_text("شناسه پرداخت (payment_id): ")
                month = input_date("ماه پرداخت جدید")
                amount = input_decimal("مبلغ جدید: ")
                call_function(conn, "SELECT update_loan_payment(%s, %s, %s)", (pid, month, amount))
                print("قسط به‌روزرسانی شد.")
            elif choice == "5":
                pid = input_text("شناسه پرداخت: ")
                if input_yes_no(f"از حذف قسط {pid} مطمئنید؟"):
                    call_function(conn, "SELECT delete_loan_payment(%s)", (pid,))
                    print("قسط حذف شد.")
            elif choice == "0":
                return
            else:
                print("گزینه نامعتبر است.")
        except psycopg2.Error as e:
            print(f"خطا: {e.pgerror or e}")


def menu_employee(conn, session):
    while True:
        print(f"\n=== منوی کارمند ({session['username']}) ===")
        print("1) مدیریت کاربران")
        print("2) مدیریت حساب‌ها")
        print("3) مدیریت وام‌ها")
        print("4) مدیریت اقساط وام")
        print("0) خروج از حساب")
        choice = input("انتخاب: ").strip()

        if choice == "1":
            menu_manage_users(conn)
        elif choice == "2":
            menu_manage_accounts(conn)
        elif choice == "3":
            menu_manage_loans(conn)
        elif choice == "4":
            menu_manage_loan_payments(conn)
        elif choice == "0":
            return
        else:
            print("گزینه نامعتبر است.")


# =====================================================================
# ADMIN MENU (everything Employee has, plus employee management)
# =====================================================================

def menu_manage_employees(conn):
    while True:
        print("\n--- مدیریت کارمندان ---")
        print("1) ساخت کارمند جدید")
        print("0) بازگشت")
        choice = input("انتخاب: ").strip()

        try:
            if choice == "1":
                uname = input_text("نام کاربری: ")
                pw = input_password("رمز عبور: ")
                fname = input_text("نام: ")
                mi = input("حرف میانی (اختیاری، یک حرف): ").strip()[:1] or None
                lname = input_text("نام خانوادگی: ")
                is_admin = input_yes_no("این کارمند ادمین باشد؟")
                call_function(
                    conn,
                    "SELECT create_employee(%s, %s, %s, %s, %s, %s)",
                    (uname, hash_password(pw), fname, mi, lname, is_admin),
                )
                print("کارمند با موفقیت ساخته شد.")
            elif choice == "0":
                return
            else:
                print("گزینه نامعتبر است.")
        except psycopg2.Error as e:
            print(f"خطا: {e.pgerror or e}")


def menu_admin(conn, session):
    while True:
        print(f"\n=== منوی ادمین ({session['username']}) ===")
        print("1) مدیریت کاربران")
        print("2) مدیریت حساب‌ها")
        print("3) مدیریت وام‌ها")
        print("4) مدیریت اقساط وام")
        print("5) مدیریت کارمندان")
        print("0) خروج از حساب")
        choice = input("انتخاب: ").strip()

        if choice == "1":
            menu_manage_users(conn)
        elif choice == "2":
            menu_manage_accounts(conn)
        elif choice == "3":
            menu_manage_loans(conn)
        elif choice == "4":
            menu_manage_loan_payments(conn)
        elif choice == "5":
            menu_manage_employees(conn)
        elif choice == "0":
            return
        else:
            print("گزینه نامعتبر است.")


# =====================================================================
# MAIN
# =====================================================================

ROLE_MENUS = {
    "User": menu_user,
    "Employee": menu_employee,
    "Admin": menu_admin,
}


def main():
    try:
        conn = get_connection()
    except psycopg2.Error as e:
        print(f"اتصال به دیتابیس ناموفق بود: {e}")
        sys.exit(1)

    print("=== سیستم بانکی ===")
    while True:
        print("\n1) ورود")
        print("2) ثبت‌نام")
        print("0) خروج از برنامه")
        choice = input("انتخاب: ").strip()

        if choice == "1":
            session = login(conn)
            if session:
                ROLE_MENUS[session["role"]](conn, session)
        elif choice == "2":
            register_user(conn)
        elif choice == "0":
            print("خداحافظ!")
            break
        else:
            print("گزینه نامعتبر است.")

    conn.close()


if __name__ == "__main__":
    main()