"""
파일 이름 : woo.py
작성일 : 2025-11-25
파일 용도 :
 MVC 패턴에서 Controller 역할

"""
from flask import Blueprint, render_template, redirect, session
# request,
from flask_dao.woo_dao import WooDAO
# woo = WooDAO()

woo_bp = Blueprint("woo", __name__)

"""
main_logout        : 
main_login         : 
category_logout    : 
category_login     : 
item               : 

"""
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# 확인용 라우터 || 이후 지워야함
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# 동기식 라우터
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

@woo_bp.route("/root")
@woo_bp.route("/home")
@woo_bp.route("/main")
@woo_bp.route("/index")
def go_main() :
    """
    # 웹 서비스 홈페이지로 이동시키기
    """
    return redirect("/")

@woo_bp.route("/")
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

    dao = WooDAO()
    ie_best_cate_li = dao.main_banner()

    user = session.get("user")





    # ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    # 문홍일 님 작업 영역 시작
    # ##### ##### ##### ##### ##### ##### ##### ##### ##### #####

    from flask_dao.mhi_dao import MhiDAO
    import json
    # 1. 변수 초기화: 그래프 오류 방지를 위해 안전한 기본값 설정
    recommended_list = []      # 캐러셀용 (Python List)
    recommendations_json = "[]" # 🚨 그래프용 (JSON String) 초기화

    if user :
        user_id = user['user_id']
        try:
            mhi_dao = MhiDAO()
            
            # 추천 데이터 로드 (Python 리스트 형태)
            recommended_list = mhi_dao.get_recommended_items_by_homogeneous_group(user_id, limit=10)
            
            # 2. Python 리스트를 JSON 문자열로 변환 (그래프용 데이터)
            if recommended_list:
                # json.dumps()를 사용해 템플릿에서 오류 없는 JSON 문자열로 변환
                recommendations_json = json.dumps(recommended_list)
            
        except Exception as e:
            # 오류 발생 시 빈 값으로 처리하여 템플릿 오류를 방지합니다.
            print(f"추천 데이터 로드 오류: {e}")
            recommended_list = []
            recommendations_json = "[]"

    # 기타 템플릿 변수 초기화
    ie_li = []
    cate_li = None

 

   # 3. 템플릿 렌더링 시 두 가지 추천 데이터를 모두 전달
    return render_template("woo/main.html",
                            best_li = ie_best_cate_li, 
                            ie_li = ie_li, 
                            cate_li = cate_li,
                            # 캐러셀에서 사용: Jinja2 for 루프에 사용
                            recommendations = recommended_list,
                            # 그래프에서 사용: Chart.js 스크립트에 사용 (가장 중요)
                            recommendations_json = recommendations_json)


    # ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
    # 문홍일 님 작업 영역 종료
    # ##### ##### ##### ##### ##### ##### ##### ##### ##### #####








@woo_bp.route("/<int:category_no>")
@woo_bp.route("/<int:category_no>/")
def category(category_no = 0) :
    """
    # 카테고리에 따라 출력 요소가 변경되어야 합니다
    
    x# 카테고리의 특정기준 1등 상품, 카테고리의 특정기준 추천 상품 1~4개 
    
    x# 로그인 되어있는 경우에는 :
    # 사용자의 구매 내역을 기준으로
    # 구매 시 높은 평점을 남길 것 같은 상품들을 추천 (6개)
    
    x# 로그인 되어있지 않는 경우에는 :
    # 카테고리의 특정기준 2~7등 상품 (6개)
    
    o# 카테고리내의 무작위 상품 12개
    """
    cate_nav(category_no)
    session["cate_no"] = category_no

    dao = WooDAO()
    ie_best_cate_li, cate_li = dao.calc_ranking_item(
            quantity = 5, option = 1, category_no = category_no
        )

    dao = WooDAO()
    ie_li = dao.cate_rand_items(category_no)

    return render_template("woo/category.html",
                            best_li = ie_best_cate_li, ie_li = ie_li, cate_li = cate_li)


#@woo_bp.route("/<int:category_no>/<int:item_no>")
#@woo_bp.route("/<int:category_no>/<int:item_no>/")
#def item(category_no = 0, item_no = 0) :
#    """
#    # 상품에 따라 상세 정보를 출력 해야합니다
#    """
#    cate_nav(category_no)
#    session["cate_no"] = category_no
#    session["item_no"] = item_no
#
#    dao = WooDAO()
#    ie = dao.load_i_info(item_no)
#
#    return render_template("woo/item.html", ie = ie)


@woo_bp.route("/<int:category_no>/<int:item_no>/cart", methods = ["GET"])
@woo_bp.route("/<int:category_no>/<int:item_no>/cart/", methods = ["GET"])
def forbid_access(category_no = 0, item_no = 0) :
    """
    # 잘못된 접근이므로 관련된 이전 페이지로 되돌려 보냅니다
    """
    session["cate_no"] = category_no
    session["item_no"] = item_no

    return redirect(f"/{category_no}/{item_no}")

@woo_bp.route("/<int:category_no>/<int:item_no>/cart", methods = ["POST"])
@woo_bp.route("/<int:category_no>/<int:item_no>/cart/", methods = ["POST"])
def add_item_to_cart(category_no = 0, item_no = 0) :
    """
    # 현재 상품 상세를 보고있는 상품을 장바구니에 담습니다
    """
    session["cate_no"] = category_no
    session["item_no"] = item_no

    user = session.get("user")
    if not user :
        return redirect("/login")

    dao = WooDAO()
    result = dao.add_i_to_c(user["user_id"], item_no)

    if result != 1 :
        return redirect("/")

    return redirect("/cart")

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# QED Temp 라우터
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

@woo_bp.route("/temp")
def temp() :
    """# DoCastingText """
    return redirect("/main")

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# 비동기식 라우터
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====



# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# 일반 함수
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
parent_li = ["fruit", "veget", "meat", "seaf", "grnut", "bread", "snack", "bever"]

def cate_nav(category_no) :
    """
    # 현재 페이지가 어떤 카테고리를 출력하는지
    # input
    # category_no : 현재 카테고리 번호 | 0미만 7초과 한다면 초기화
    # return
    # str ( 카테고리 이름 )
    """
    session.pop("parent", None)
    if category_no >= 0 and category_no <= 7 :
        parent = parent_li[category_no]
        session["parent"] = {}
        session["parent"][parent] = "class=active"
