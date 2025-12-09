from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_dao.mhi_dao import MhiDAO
import json

from flask_dao.woo_dao import WooDAO
from routes.woo import cate_nav

dao = MhiDAO()  # DAO 인스턴스 생성
mhi_bp = Blueprint('mhi', __name__)


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
        return redirect(url_for("mhi.main"))
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

    return redirect(url_for("mhi.main"))

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
@mhi_bp.route("/")
def main() :
    """
    # url 의 root 에 해당하는 경로
    # 각 대분류별 역대 최고 평가 상품이 출력 되어야 합니다
    
    x# 로그인 되어있는 경우에는 :
    # user 의 관심사에 따라 출력 요소가 변경되어야 합니다
    # "나"의 구매목록을 기준으로 관심도를 추론해서 상품 6개가 출력 되어야 합니다
    # "나" 와 유사한 사용자간의 구매목록을 특이값 분해해서 출력 되어야 합니다
    
    o# 로그인 되어있지 않는 경우에는 :
    # 웹서비스 내에서 역대 최고 평가 상위 6개 가 출력 되어야 합니다
    """
    cate_nav(-1)

    wdao = WooDAO()
    best_li = wdao.main_banner()

    user = session.get("user")
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
# 문홍일 님 작업 영역 시작
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    if user :
        # 1. 변수 초기화: 그래프 오류 방지를 위해 안전한 기본값 설정
        recommended_list = []      # 캐러셀용 (Python List)
        recommendations_json = "[]" # 🚨 그래프용 (JSON String) 초기화

        # 기타 템플릿 변수 초기화
        ie_li = []
        cate_li = None

        user_id = user['user_id']
        try:
            # 추천 데이터 로드 (Python 리스트 형태)
            recommended_list = dao.get_recommended_items_by_homogeneous_group(user_id, limit=10)

            # 2. Python 리스트를 JSON 문자열로 변환 (그래프용 데이터)
            if recommended_list:
                # json.dumps()를 사용해 템플릿에서 오류 없는 JSON 문자열로 변환
                recommendations_json = json.dumps(recommended_list)

        except Exception as e:
            # 오류 발생 시 빈 값으로 처리하여 템플릿 오류를 방지합니다.
            print(f"추천 데이터 로드 오류: {e}")
            recommended_list = []
            recommendations_json = "[]"

         # 3. 템플릿 렌더링 시 두 가지 추천 데이터를 모두 전달
        return render_template("woo/main.html",
                            best_li = best_li,
                            ie_li = ie_li,
                            cate_li = cate_li,
                            # 캐러셀에서 사용: Jinja2 for 루프에 사용
                            recommendations = recommended_list,
                            # 그래프에서 사용: Chart.js 스크립트에 사용 (가장 중요)
                            recommendations_json = recommendations_json)
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
# 문홍일 님 작업 영역 종료
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####

# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
# ujin 님 작업 영역 시작
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    if not user :
        wdao = WooDAO()
        ie_li, cate_li = wdao.calc_ranking_item(quantity = 6)

        ie_li = []
        cate_li = None
        target_keys = [
            'item_name', 'item_rate', 'trust_score', 'item_reviewcnt'
        ]
        name = []
        rate = []
        trust = []
        review = []
        for item in ie_li :
            name.append(item[target_keys[0]])
            rate.append(item[target_keys[1]])
            trust.append(item[target_keys[2]])
            review.append(item[target_keys[3]])

        column_chart_data = [ name, rate, trust, review ]

        return render_template("woo/main.html",
                                best_li = best_li, ie_li = ie_li, cate_li = cate_li,
                                column_chart_data = column_chart_data)
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
# ujin 님 작업 영역 종료
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####


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

# routes/mhi.py 파일 하단에 추가

# ------------------- 연령대/성별 기반 추천 페이지 -------------------
@mhi_bp.route("/group_recommend")
def group_recommend():
    # 1. 로그인 여부 확인
    # 'user' 세션 키를 사용하고 있으므로, 이를 확인합니다.
    if 'user' not in session:
        flash("추천 서비스를 이용하려면 로그인해주세요.")
        return redirect(url_for("mhi.login_get"))

    user_id = session['user']['user_id']
    
    # 2. DAO 메서드 호출
    # dao는 이미 파일 상단에 MhiDAO()로 인스턴스화 되어 있습니다.
    try:
        # get_recommended_items_by_group 메서드를 호출
        recommended_list = dao.get_recommended_items_by_homogeneous_group(user_id, limit=10)
    except Exception as e:
        # DB 오류나 데이터 처리 오류 발생 시
        print(f"추천 데이터 로드 오류: {e}")
        flash("추천 정보를 불러오는 데 실패했습니다.")
        recommended_list = []

    # 3. 템플릿 렌더링
    # 'mhi' 폴더 내에 템플릿을 두거나, templates/group_recommend.html로 설정할 수 있습니다.
    # 여기서는 'mhi/group_recommend.html'을 가정합니다.
    return render_template(
        "mhi/group_recommend.html", 
        recommendations=recommended_list
    )