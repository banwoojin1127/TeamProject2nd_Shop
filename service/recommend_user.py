import datetime
import numpy as np
import pandas as pd
from collections import Counter
from flask import current_app
from flask_dao.lsh_dao import LshDAO

def recommend_user(target_user: str, top_n=5):

    EMPTY_RESULT = {
        "target_user": target_user,
        "recommendations": [],
        "graph": {"labels": [], "values": []}
    }

    dao = LshDAO()

    # 유저 정보 가져오기 (Dict 형태)
    row = dao.get_user_info(target_user)
    if not row:
        dao.close()
        return EMPTY_RESULT

    birth = row.get("birth")
    gender = row.get("gender")

    # birth 파싱
    if isinstance(birth, str):
        try:
            birth = datetime.datetime.strptime(birth, "%Y-%m-%d").date()
        except Exception as e:
            dao.close()
            return EMPTY_RESULT

    if not birth:
        dao.close()
        return EMPTY_RESULT

    year = birth.year

    # 유사 사용자 그룹
    user_group = dao.get_homogeneous_users(gender, year, target_user)
    if not user_group:
        user_group = dao.get_all_users_except(target_user)

    # 구매 내역 조회 (상품, 가격, 평점, 이미지, 카테고리)
    rows = dao.get_purchase_history_by_users(user_group)
    if not rows:
        dao.close()
        return EMPTY_RESULT

    df = pd.DataFrame(rows, columns=["item_id", "item_name", "item_rate", "item_price", "item_img", "item_category"])
    df = df.fillna("")
    df["item_name"] = df["item_name"].str.strip()

    # 본인 구매 목록
    my_items = dao.get_user_purchase_set(target_user)
    if not my_items:
        dao.close()
        return EMPTY_RESULT

    # Jaccard 유사도 계산
    sim_scores = {}
    for uid in user_group:
        u_items = dao.get_user_purchase_set(uid)
        if not u_items:
            continue
        inter = len(my_items & u_items)
        union = len(my_items | u_items)
        sim_scores[uid] = inter / union if union else 0

    # 유사도 Top10
    top_users = sorted(sim_scores.items(), key=lambda x: x[1], reverse=True)[:10]
    top_user_ids = [u for u, s in top_users]

    # 추천 후보 pool
    pool = []
    for uid in top_user_ids:
        for iid in dao.get_user_purchase_set(uid):
            if iid not in my_items:
                pool.append(iid)

    if not pool:
        dao.close()
        return EMPTY_RESULT

    # 가장 많이 구매된 Top N 상품
    freq = Counter(pool)
    rec_ids = [i for i, c in freq.most_common(top_n)]

    # 추천 DF 추출 (가격, 평점 포함)
    recs = df[df["item_id"].isin(rec_ids)][["item_id", "item_name", "item_img", "item_price", "item_rate", "item_category"]]
    recs = recs.drop_duplicates("item_id").head(top_n)

    # 추천 목록 정리
    recommendations = [
        {
            "item_id": int(iid),
            "item_name": name,
            "item_img": img,
            "item_price": int(price) if price not in (None, "") else 0,
            "item_rate": float(rate) if rate not in (None, "") else 0.0,
            "item_category": category
        }
        for iid, name, img, price, rate, category in recs.values
    ]

    # 그래프용 데이터
    labels = [r["item_name"] if len(r["item_name"]) <= 12 else r["item_name"][:12] + "..." for r in recommendations]
    values = []
    user_sets = {uid: dao.get_user_purchase_set(uid) for uid in top_user_ids}
    for iid in rec_ids:
        sim_list = [sim_scores.get(uid, 0) for uid, items in user_sets.items() if iid in items]
        values.append(round(np.mean(sim_list), 4) if sim_list else 0)

    graph_data = {"labels": labels, "values": values}

    # 결과 캐싱
    result = {
        "target_user": target_user,
        "recommendations": recommendations,
        "graph": graph_data
    }

    current_app.recommend_user_result = result
    dao.close()
    
    return result
