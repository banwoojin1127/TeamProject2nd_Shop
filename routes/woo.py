"""
파일 이름 : woo.py
작성일 : 2025-11-25
파일 용도 :
 MVC 패턴에서 Controller 역할

"""
#import json
from flask import Blueprint, render_template, redirect, session, url_for, request, jsonify
# request,
from flask_dao.woo_dao import WooDAO
# woo = WooDAO()

from service.woo.for_gemini import WooGemini
wodel = WooGemini()

woo_bp = Blueprint("woo", __name__)

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
    return redirect(url_for('mhi.main'))

COMMENT_MAIN_PAGE_ROUTE = '''
#@woo_bp.route("/")
#def main() :
#    """
#    # url 의 root 에 해당하는 경로
#    # 각 대분류별 역대 최고 평가 상품이 출력 되어야 합니다
#
#    ?# 로그인 되어있는 경우에는 :
#    # user 의 관심사에 따라 출력 요소가 변경되어야 합니다
#    # "나"의 구매목록을 기준으로 관심도를 추론해서 상품 6개가 출력 되어야 합니다
#    # "나" 와 유사한 사용자간의 구매목록을 특이값 분해해서 출력 되어야 합니다
#
#    o# 로그인 되어있지 않는 경우에는 :
#    # 웹서비스 내에서 역대 최고 평가 상위 6개 가 출력 되어야 합니다
#    """
#   cate_nav(-1)
#
#    dao = WooDAO()
#    best_li = dao.main_banner()
#
#    user = session.get("user")
#
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
# ujin 님 작업 영역 시작
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
#    if not user :
#        ie_li = []
#        cate_li = None

#        dao = WooDAO()
#        ie_li, cate_li = dao.calc_ranking_item(quantity = 6)
#
#        target_keys = [
#            'item_name', 'item_rate', 'trust_score', 'item_reviewcnt'
#        ]
#        name = []
#        rate = []
#        trust = []
#        review = []
#        for item in ie_li :
#            name.append(item[target_keys[0]])
#            rate.append(item[target_keys[1]])
#            trust.append(item[target_keys[2]])
#            review.append(item[target_keys[3]])
#
#        column_chart_data = [ name, rate, trust, review ]
#
#        return render_template("woo/main.html",
#                                best_li = best_li, ie_li = ie_li, cate_li = cate_li,
#                                column_chart_data = column_chart_data)
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
# ujin 님 작업 영역 종료
# ##### ##### ##### ##### ##### ##### ##### ##### ##### #####
'''


@woo_bp.route("/<int:category_no>")
@woo_bp.route("/<int:category_no>/")
def category(category_no = 0) :
    """
    # 카테고리에 따라 출력 요소가 변경되어야 합니다
    
    o# 현재 카테고리에 해당하는 역대 최고 평가 상품 8개 
    
    x# 로그인 되어있는 경우에는 :
    # 사용자의 구매 내역을 기준으로
    # 구매 시 높은 평점을 남길 것 같은 상품들을 추천 (6개)
    # 이었는데 API 로 Gemini 한테 물어보기
    
    o# 로그인 되어있지 않는 경우에는 :
    # 카테고리의 특정기준 9~14등 상품 (6개)
    
    o# 카테고리내의 무작위 상품 12개
    """
    cate_nav(category_no)
    session["cate_no"] = category_no


    dao = WooDAO()
    best_li, cate_li = dao.calc_ranking_item(
            quantity = 8, option = 1, category_no = category_no
        )

    dao = WooDAO()
    ie_li = dao.cate_rand_items(category_no)

    user = session.get("user")
    if user :
        user_id = user.get("user_id")
        recommend_plan = wodel.recommend_cate_in_parent(user_id, category_no)
        print(recommend_plan)

        return render_template("woo/category.html",
                                best_li = best_li, ie_li = ie_li, cate_li = cate_li)

    else :

        # ?????

        return render_template("woo/category.html",
                                best_li = best_li, ie_li = ie_li, cate_li = cate_li)

COMMENT_ITEM_PAGE_ROUTE = '''
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
'''

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
# ------------------------------
# 무한 스크롤
# ------------------------------
@woo_bp.route("/api/items/<int:category_no>")
def api_scroll(category_no):
    """
    api_scroll의 Docstring
    
    :param category_no: 설명
    :return: 설명
    :rtype: Response
    """
    session["cate_no"] = category_no

    # 함수 안에서 URL index → DB parent_id 매핑
    url_index_to_parent_id = {
        0: 1,  # 과일
        1: 2,  # 채소
        2: 3,  # 고기
        3: 4,  # 해산물
        4: 5,  # 견과류
        5: 6,  # 빵/곡류
        6: 7,  # 스낵
        7: 8,  # 음료
    }
    parent_id = url_index_to_parent_id.get(category_no, 1)  # 기본값 1

    page = int(request.args.get("page", 1))
    per_page = 20
    offset = (page - 1) * per_page

    dao = WooDAO()
    items = dao.get_items_by_parent(parent_id, offset, per_page)

    return jsonify(items)


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

        # ------------------------------

