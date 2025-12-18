import numpy as np
from collections import defaultdict
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity

from flask_dao.lsh_dao import LshDAO


def recommend_purchase(
    target_user,
    period="weekly",
    user_top_n=5,
    item_top_k=6
):
    dao = LshDAO()

    # ================== 1. 기간별 구매 이력 ==================
    history_rows = dao.get_purchase_history_all_by_period(period)

    if not history_rows:
        dao.close()
        return {"error": "구매 이력이 없습니다."}

    user_list = sorted({r["user_id"] for r in history_rows})
    item_list = sorted({r["item_id"] for r in history_rows})

    user_idx = {u: i for i, u in enumerate(user_list)}
    item_idx = {iid: i for i, iid in enumerate(item_list)}

    if target_user not in user_idx:
        dao.close()
        return {"error": "해당 기간에 구매 이력이 없습니다."}

    # ================== 2. 희소 행렬 ==================
    rows = [user_idx[r["user_id"]] for r in history_rows]
    cols = [item_idx[r["item_id"]] for r in history_rows]
    data = np.ones(len(history_rows))

    mat = csr_matrix(
        (data, (rows, cols)),
        shape=(len(user_list), len(item_list))
    )

    # ================== 3. SVD ==================
    n_components = max(1, min(20, min(mat.shape) - 1))
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    user_factors = normalize(svd.fit_transform(mat))

    # ================== 4. 유사 사용자 ==================
    target_vec = user_factors[user_idx[target_user]]
    sims = cosine_similarity(target_vec.reshape(1, -1), user_factors).flatten()
    sims[user_idx[target_user]] = -1

    top_indices = sims.argsort()[::-1][:user_top_n]
    similar_users = [user_list[i] for i in top_indices]

    # ================== 4-1. 타겟 유저 구매 상품 ==================
    target_user_items = {
        r["item_id"] for r in history_rows
        if r["user_id"] == target_user
    }

    # ================== 5. 유사 사용자 TOP 상품 ==================
    top_items = dao.get_top_items_from_users_by_period(
        similar_users,
        period,
        top_n=item_top_k * 2   # ← 여유 있게 더 가져옴
    )

    dao.close()

    # ================== 6. 타겟 유저 구매 상품 제외 ==================
    filtered_items = [
        r for r in top_items
        if r["item_id"] not in target_user_items
    ]

    # ================== 6-1. 카테고리 과다 추천 방지 ==================
    MAX_PER_CATEGORY = 2
    category_count = defaultdict(int)
    diversified_items = []

    for r in filtered_items:
        cat = r["item_category"]

        if category_count[cat] >= MAX_PER_CATEGORY:
            continue

        diversified_items.append(r)
        category_count[cat] += 1

        if len(diversified_items) >= item_top_k:
            break

    # ================== 7. 추천 상품 ==================
    recommended_items = [{
        "item_id": r["item_id"],
        "item_name": r["item_name"],
        "item_price": r["item_price"],
        "item_category": r["item_category"],
        "item_img": r["item_img"],
        "purchase_count": r["cnt"]
    } for r in diversified_items]

    # ================== 8. Chart 데이터 ==================
    return {
        "target_user": target_user,
        "similar_users": similar_users,
        "recommended_items": recommended_items,
        "chart": {
            "labels": [i["item_name"] for i in recommended_items],
            "values": [i["purchase_count"] for i in recommended_items]
        }
    }

