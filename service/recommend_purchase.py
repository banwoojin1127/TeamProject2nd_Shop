import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity

from flask_dao.lsh_dao import LshDAO

def recommend_purchase(target_user, user_top_n=5, item_top_k=6):

    dao = LshDAO()

    # ================== 1. 전체 구매 이력 조회 ==================
    # user_id, item_id
    history_rows = dao.get_purchase_history_all()

    # item_id, item_name, item_img, item_category
    item_rows = dao.get_items_all()

    # item_id → item_name 매핑
    item_name_map = {row["item_id"]: row["item_name"] for row in item_rows}

    # 사용자 / 상품 목록 생성
    user_list = sorted(set([r["user_id"] for r in history_rows]))
    item_list = sorted(set([r["item_id"] for r in history_rows]))

    user_idx = {u: i for i, u in enumerate(user_list)}
    item_idx = {iid: i for i, iid in enumerate(item_list)}

    # ================== 2. 희소 행렬 생성 ==================
    rows = [user_idx[r["user_id"]] for r in history_rows]
    cols = [item_idx[r["item_id"]] for r in history_rows]
    data = np.ones(len(history_rows))

    mat = csr_matrix((data, (rows, cols)),
                     shape=(len(user_list), len(item_list)))

    # ================== 3. SVD 학습 ==================
    n_components = max(1, min(20, min(mat.shape) - 1))
    svd = TruncatedSVD(n_components=n_components, random_state=42)

    user_factors = normalize(svd.fit_transform(mat))

    if target_user not in user_idx:
        return {"error": f"'{target_user}'는 존재하지 않는 사용자입니다."}

    # ================== 4. 유사 사용자 계산 ==================
    target_vec = user_factors[user_idx[target_user]]
    sims = cosine_similarity(target_vec.reshape(1, -1), user_factors).flatten()

    sims[user_idx[target_user]] = -1  # 자기 자신 제외
    top_indices = sims.argsort()[::-1][:user_top_n]

    similar_users = [user_list[i] for i in top_indices]

    # ================== 5. DAO에서 유사 사용자 그룹의 TOP 상품 조회 ==================
    top_items = dao.get_top_items_from_users(similar_users, top_n=item_top_k)
    dao.close()

    # ================== 6. 추천 상품 데이터 구조 생성 ==================
    recommended_items = []
    for row in top_items:
        recommended_items.append({
            "item_id": row["item_id"],
            "item_name": row["item_name"],
            "item_price": row["item_price"],
            "item_category": row["item_category"],
            "item_img": row["item_img"],
            "purchase_count": row["cnt"]
        })

    # ================== 7. Chart.js 용 데이터 ==================
    chart_labels = [item["item_name"] for item in recommended_items]
    chart_values = [item["purchase_count"] for item in recommended_items]

    # ================== 8. 최종 반환 ==================
    return {
        "target_user": target_user,
        "similar_users": similar_users,
        "recommended_items": recommended_items,
        "chart": {
            "labels": chart_labels,
            "values": chart_values
        }
    }
