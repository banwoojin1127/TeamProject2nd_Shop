"""
파일 이름 : for_gemini.py
작성 날짜 : 2025-12-10
파일 용도 :
 API 로 Google AI Studio Service 를 활용하기 위함 

"""
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# !!! import
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

# .json 파일 사용하기 위함
import json

# dotenv 의 load_dotenv() 를 활용해야
# os 에서 getenv() 를 통해 .env 의 값을 가져올 수 있음
import os
from dotenv import load_dotenv

# Google AI Studio Service 중 Gemini 를 활용하기 위함
import google.generativeai as genai

# 카테고리 (대분류, 소분류) 값 쉽게 구하기 위함
import service.woo.cate_extractor as cateract

# API 용으로 DB 에서 Data 를 맞춤으로 조회하기 위함
from service.woo.with_gemini import WithAPI

# JSON 파일 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATE_LIST_JSON_PATH = os.path.join(BASE_DIR, 'data', 'category_list.json')
CATE_LIST_JSON = None

# 파일을 열고 JSON 데이터를 로드합니다.
try:
    with open(CATE_LIST_JSON_PATH, 'r', encoding='utf-8') as f:
        # json.load(f): 파일 객체(f) 전체를 읽어 딕셔너리 리스트로 변환
        CATE_LIST_JSON = json.load(f)

    print("# " + "=" * 50)
    print("Debug | File for_gemini | Field : JSON Load OK")
    print(f"Debug | JSON Load OK : { type(CATE_LIST_JSON) }")
    print("# " + "=" * 50)

except Exception as e :
    print("# " + "=" * 50)
    print("Debug | File for_gemini | Field : !!! ERROR !!!")
    print(f"Debug | ERROR : { e }")
    print("# " + "=" * 50)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# !!! Service Logic Class
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
class WooGemini :
    """
    API 로 Google AI Studio Service 를 활용하기위한 기준 Class
    """
    # ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
    # !!! Class Field
    # ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

    # 싱글톤 패턴을 위해서
    # 클래스를 담음
    _singleton = None

    # 싱글톤 패턴시 init 반복호출 방지
    # 호출 여부를 담음
    _flaginit = False


    # ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
    # !!! 생성자
    # ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
    def __new__(cls, *args, **kwargs):
        """
        __new__의 Docstring
        """
        if cls._singleton is None :
            cls._singleton = super().__new__(cls)
        return cls._singleton

    def __init__(self):
        """
        # WooGemini 의 생성자
        # 호출시 API 연결, DB 연결
        """
        if not self._flaginit :
            # .env 파일의 내용을 환경 변수로 로드
            # 파일 위치를 자동으로 찾음
            load_dotenv()

            # os.getenv를 사용하여 값을 가져옴
            self.api_key = os.getenv("UJ_GOOGLE_API_KEY")
            self.db_url = os.getenv("DATABASE_URL")

            # 값을 확인하고 연결
            try :
                if self.api_key :
                    genai.configure(api_key = self.api_key)
                    self.wodelgemini = genai.GenerativeModel("gemini-2.5-flash")
                    self._flaginit = True
                    print("# " + "=" * 50)
                    print("Debug | Class WooGemini | if is key : Ok")
                    print("# " + "=" * 50)
                else:
                    print("# " + "=" * 50)
                    print("Debug | Class WooGemini | if is key : API Key not found!")
                    print("# " + "=" * 50)

            except Exception as e :
                print("# " + "=" * 50)
                print("Debug | Class WooGemini | __init__() : !!! ERROR !!!")
                print(f"Debug | ERROR : { e }")
                print("# " + "=" * 50)

            finally :
                pass
        else :
            print("# " + "=" * 50)
            print("Debug | Class WooGemini | if not flag : Already call __init__()")
            print("# " + "=" * 50)


    # ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
    # !!! 함수 ( 메서드 )
    # ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

    def recommend_cate_in_parent(self, user_id, parent_id) :
        """
        # 사용자 pKey, 대분류 값을 받아
        # API 를 호출하여 질의응답 하고
        # "추천전략" 과 "추천답변" 을 반환
        """

        dao = WithAPI()
        purchase_li = dao.for_recommend_cate_in_parent(user_id)

        prompt = f"""
            역할 : 당신은 마트의 쇼핑 AI 분석가입니다.

            [ 입력 데이터 ]
            사용자 구매내역 리스트 : {purchase_li}
            소분류 리스트 : {choice_category(parent_id)}

            [ 지시 사항 ]
            '사용자 구매내역 리스트'의 정보를 분석하고, 추천 할 만한 상품을 '소분류 리스트'에서 반드시 3개만 선택하세요.
            '사용자 구매내역 리스트'에서 'total_sales' (판매 수량) 이 많은 항목 순으로 가능한한 연관지어서 생각하세요.
            특정한 대분류의 페이지에 추천하는 것이므로 '소분류 리스트'에 없는 상품은 절대 선택하지마세요.
            논리적이고 일반적인 과정을 통한 추천인지 반드시 확인하세요.
            '추천전략'은 관리자를 위한 설명입니다.
            선택한 추천 상품에 대한 추천 이유를 사용자에게 한문장으로 소개하세요.
            결과는 오직 JSON으로도 변환이 쉬운 Dictionary 형식으로만 출력하세요.

            [ 출력 Dictionary 예시 ]
            {{
                "추천전략" : [
                    "추천전략A", "추천전략B", ...
                ],
                "추천답변" : [
                    {{ "item_category" : sub_category_id, "reason" : "추천 이유 설명" }},
                    {{ "item_category" : sub_category_id, "reason" : "추천 이유 설명" }},
                    ...
                ]
            }}

            [ 출력 예시 보강 ]
            출력 예시에서 sub_category_id 는 integer 입니다.
        """

        answer = self.wodelgemini.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        recommend_plan = None
        try :
            recommend_plan = json.loads(answer.text)

            print("# " + "=" * 50)
            print("Debug | Class WooGemini | recommend_cate_in_parent() : json.loads Ok")
            print("# " + "=" * 50)

        except Exception as e :
            print("# " + "=" * 50)
            print("Debug | Class WooGemini | recommend_cate_in_parent() : !!! ERROR !!!")
            print(f"Debug | ERROR : { e }")
            print("# " + "=" * 50)

        return recommend_plan

    # ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
    # !!! Templaet 함수 ( 메서드 ) QED
    # ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

    def temp(self) :
        """
        # Temp의 Docstring
        """



        return None


    # ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
    # !!!
    # ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# !!! ?????
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

def choice_category(perent_id) :
    """
    # 대분류 받아서 소분류의 pKey 랑 name 반환
    """

    cate_id_li = cateract.parent_to_cate_list(perent_id)

    cate_li = [
        {
            "sub_category_id" : category_li[cate_id_val - 1]["category_id"],
            "sub_category_name" : category_li[cate_id_val - 1]["category_name"]
        }
        for cate_id_val in cate_id_li
    ]

    return cate_li

category_li = CATE_LIST_JSON["category_list"]
