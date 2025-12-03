from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_dao.mhi_dao import MhiDAO

mhi_bp = Blueprint('mhi', __name__)
dao = MhiDAO()  # DAO 인스턴스 생성

# ------------------- JSON 데이터받기 -------------------
# 자동으로 비밀번호 입력을 위함
@mhi_bp.route("/get_users")
def get_users():
    users = dao.get_all_users()
    users_dict = {u['user_id']: u['user_pw'] for u in users}
    return jsonify(users_dict)

# DAO에서 모든 user_id만 리스트로 가져와 JSON으로 반환
# 드롭다운에 들어갈 아이디를 가져오기 위함
@mhi_bp.route("/get_user_ids")
def get_user_ids_route():
    return jsonify(dao.get_user_ids())

# ------------------- 로그인 페이지 -------------------
@mhi_bp.route("/login", methods=["GET"])
def login_get():
    return render_template("mhi/login.html", user_id=session.get("user_id"))

# ------------------- 로그인 처리 -------------------
@mhi_bp.route("/login", methods=["POST"])
def login_post():
    user_id = request.form.get("user_id", "").strip()
    user_pw = request.form.get("user_pw", "").strip()

    user_data = dao.check_login_and_get_user(user_id, user_pw)
    if user_data:
        #세션 업데이트
        session["user"] = user_data
        """
        session.update({
            'user_id': user_data['user_id'],
            'user_name': user_data['user_name'],
            'gender': user_data.get('gender'),
            'birth': str(user_data.get('birth')) if user_data.get('birth') else None
        })
        """
        return redirect(url_for("woo.main"))
    else:
        flash("아이디 또는 비밀번호가 잘못되었습니다.")
        return redirect(url_for("mhi.login_get"))

# ------------------- 로그아웃 -------------------
@mhi_bp.route("/logout", methods=["POST"])
def logout():
    # 현재 로그인한 유저의 세션 정보만 삭제
    session.pop("user")
    """
    for key in ['user_id', 'user_name', 'gender', 'birth']:
        session.pop(key, None)
    """

    return redirect(url_for("woo.main"))

# # ------------------- 홈 페이지 -------------------
# @mhi.route("/")
# def home():
#     user_name = session.get("user_name")
#     user_id = session.get("user_id")

#     user_count = 42
#     product_count = 120
#     today_visitors = 15

#     return render_template(
#         "home.html",
#         user_id=user_id,
#         user_name=user_name,
#         user_count=user_count,
#         product_count=product_count,
#         today_visitors=today_visitors
#     )


@mhi_bp.route("/signup", methods=["GET"])
def signup_get():
    return render_template("mhi/signup.html")


@mhi_bp.route("/signup", methods=["POST"])
def signup_post():
    user_id = request.form.get("user_id", "").strip()
    user_pw = request.form.get("user_pw", "").strip()
    user_name = request.form.get("user_name", "").strip()
    gender = request.form.get("gender")
    birth = request.form.get("birth")

    # 1) 아이디 중복 체크
    if dao.get_user_by_id(user_id):
        flash("이미 존재하는 아이디입니다.")
        return redirect(url_for("mhi.signup_get"))

    # 2) DB 저장
    success = dao.create_user(user_id, user_pw, user_name, gender, birth)
    if not success:
        flash("회원가입 중 오류가 발생했습니다.")
        return redirect(url_for("mhi.signup_get"))

    flash("회원가입이 완료되었습니다! 이제 로그인해주세요.")
    return redirect(url_for("mhi.login_get"))