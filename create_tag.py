from konlpy.tag import Okt
import re
from flask_dao.lsh_dao import LshDAO

okt = Okt()

def extract_tags(item_name):
    cleaned = re.sub(r"\([^)]*\)", "", item_name)
    cleaned = re.sub(r"\d+kg|\d+g|\d+과|[\d,.]+", "", cleaned)

    nouns = okt.nouns(cleaned)

    stopwords = ["용", "봉", "입", "박스", "팩", "무료배송", "세트", "상품", "기획", "특", "대", "중소", "중대",
            "중", "소", "kg", "g", "정품", "산지직송", "가정용", "선물", "특가", "과", "가정", "더", "내외", "포장",
            "당일", "수확", "품질", "보장", "올해", "제스", "프리", "쇼핑", "프리미엄", "때깔", "플러스", "아빠", "실속",
            "마음", "엄마", "할머니", "할아버지", "미소", "웃음", "년산", "우체국", "인증", "마을", "맑은", "용량",
            "라벨", "스토리", "일품", "오늘", "내일", "혼자", "먹기", "테이블", "컷팅", "커팅", "등급", "돌핀", "개입", 
            "최고급", "황금", "리뷰", "발송", "출하", "경력", "선택", "사이즈", "옵션", "인기", "모음", "봉지", "유통",
            "기한", "구매", "병입", "쿠폰", "할인", "알뜰", "폭탄", "증정", "구성", "생산자", "사은", "이벤트", "마리",
            "수능", "지퍼", "각개", "이상", "이하", "보증"]
    
    # 불용어 제거
    nouns = [n for n in nouns if n not in stopwords and len(n) > 1]

    # 중복 제거 (순서 유지)
    seen = set()
    unique_nouns = []
    for n in nouns:
        if n not in seen:
            unique_nouns.append(n)
            seen.add(n)

    return unique_nouns


def insert_tag_from_db():
    dao = LshDAO()

    items = dao.get_items_all_name()

    for item_id, item_name in items:
        tags = extract_tags(item_name)
        tag_str = ",".join(tags)

        dao.update_item_tag(item_id, tag_str)
        print(f"[저장됨] {item_id}: {tag_str}")

    dao.close()


if __name__ == "__main__":
    insert_tag_from_db()
