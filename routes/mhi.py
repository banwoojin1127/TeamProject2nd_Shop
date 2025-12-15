from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_dao import mhi_dao
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
    # 로그인 시: 유사 사용자 기반 추천 목록 (3가지 순위 기준)을 출력
    # 비로그인 시: 웹서비스 내 역대 최고 평가 상위 6개 출력
    """
    cate_nav(-1)

    wdao = WooDAO()
    best_li = wdao.main_banner() # 비로그인 시 사용될 전체 최고 평가 상품

    user = session.get("user")
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
# 문홍일 님 작업 영역 시작
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####

    # ##### 로그인한 경우 #####
    ie_li = []
    cate_li = None
    
    # 기본값 설정
    recommendations_carousel = []   # 캐러셀 (구매 횟수 기준 사용)
    recommendations_list = []       # 리스트 (별점 기준 사용)
    weighted_recommendations_list = [] # 추가된 가중치 순위 리스트
    recommendations_json = json.dumps([]) # 차트용 JSON

    if user:
        user_id = user['user_id']
        
        # --------------------------------------------------------
        # ⭐ 1. DAO를 한 번만 호출하여 세 가지 정렬 리스트를 모두 받기
        # --------------------------------------------------------
        recommendation_data = dao.get_recommended_items_by_homogeneous_group(user_id, limit=100)
        
        if recommendation_data and recommendation_data.get('rating_list'):
            
            # 2. 각 리스트 추출
            purchase_list = recommendation_data['purchase_list'] # 구매 횟수 순위
            rating_list = recommendation_data['rating_list']     # 별점 순위
            weighted_list = recommendation_data['weighted_list'] # 가중치 순위

            # 3. 각 용도에 맞게 매핑
            
            # - 캐러셀용: 구매 횟수 순위 사용
            recommendations_carousel = purchase_list
            
            # - 메인 리스트용: 별점 순위 사용
            recommendations_list = rating_list
            
            # - 가중치 평점 리스트용: 가중치 순위 사용
            weighted_recommendations_list = weighted_list
                        
            # - 차트용 JSON: 가중치 순위 목록 사용
            recommendations_json = json.dumps(weighted_list) 

        return render_template(
            "woo/main.html",
            best_li=best_li,
            ie_li=ie_li,
            cate_li=cate_li,
            # -------------------------------------------------
            # ⭐ 템플릿에 전달할 추천 목록
            # -------------------------------------------------
            # 1) 캐러셀 (구매 횟수 순위)
            recommendations_carousel=recommendations_carousel,
            
            # 2) 별점 순위 리스트 (기존 rank.html에서 사용)
            recommendations_list=recommendations_list,
            
            # 3) 가중치 순위 리스트 (새로운 템플릿에서 사용)
            weighted_recommendations_list=weighted_recommendations_list,
            
            # 4) 차트용 JSON
            recommendations_json=recommendations_json
            
            
        )


# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
# 문홍일 님 작업 영역 종료
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####

# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
# ujin 님 작업 영역 시작
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    if not user :
        ie_li = []
        cate_li = None
        
        wdao = WooDAO()
        ie_li, cate_li = wdao.calc_ranking_item(quantity = 6)

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



