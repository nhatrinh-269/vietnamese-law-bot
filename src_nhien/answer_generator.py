"""
prompt_builder.py
"""

from LLM_gemini import LLM_gemini


def build_free_prompt(histories: str,
                      question: str,
                      results_ds: str,
                      results_hs: str) -> str:
    """
    Build a concise prompt for 'free' plan: short answer, limited length.
    """
    return f"""
            GÓI FREE: Trả lời ngắn gọn, không quá nhiều thông tin, giới hạn độ dài.

            Bạn là luật sư chuyên về Bộ luật Dân sự và Bộ luật Hình sự Việt Nam. Hãy trả lời ngắn gọn dựa trên các điều luật sau:

            > Lịch sử trao đổi:
            > {histories}

            *Câu hỏi:* "{question}"

            *Điều luật tham khảo:*
            - Bộ luật Dân sự: {results_ds}
            - Bộ luật Hình sự: {results_hs}

            _Trả lời ngắn gọn, tom tat theo điều luật có liên quan, luot bo cac dieu luat khong can thiet di. chi can 2,3,4 dieu la duoc, không thêm suy đoán._
            """


def build_pro_prompt(histories: str,
                     question: str,
                     results_ds: str,
                     results_hs: str) -> str:
    """
    Build a detailed prompt for 'pro' plan: detailed analysis and citations.
    """
    return f"""
            GÓI PRO: Trả lời chi tiết, phân tích và trích dẫn 1/2 các điều luật quan trong, trình bày vai trường hợp liên quan.

            Bạn là luật sư chuyên về Bộ luật Dân sự và Bộ luật Hình sự Việt Nam. Hãy phân tích và trả lời câu hỏi dựa trên điều luật sau:

            > Lịch sử trao đổi:
            > {histories}

            **Câu hỏi:** "{question}"

            **Điều luật tham khảo:**
            - Bộ luật Dân sự: {results_ds}
            - Bộ luật Hình sự: {results_hs}

            **Yêu cầu:**
            1. Trích dẫn rõ số và nội dung điều luật.
            2. Phân tích chi tiết, chi phan tich dieu luat so voi cau hoi, khong neu vi du.
            3. Kết luận rõ ràng.
            4. Tránh suy đoán ngoài dữ liệu**, chỉ trả lời dựa trên thông tin đã truy vấn được.  
            _Trả lời chỉ dựa trên dữ liệu truy vấn, không suy đoán ngoài._
            """


def build_premium_prompt(histories: str,
                         question: str,
                         results_ds: str,
                         results_hs: str) -> str:
    """
    Build an in-depth prompt for 'premium' plan: comprehensive prompt using original template.
    """
    return f"""
            plan type = free, pro, premium
            user_plan_type = premium
            khong in plan type ra
            GÓI FREE: Trả lời ngắn gọn, khong qua nhieu thong tin, giới hạn độ dài.
            GÓI PRO: Trả lời chi tiết, phân tích và trích dẫn các điều luật đầy đủ, trình bày các trường hợp liên quan.
            GÓI PREMIUM: Trả lời chuyên sâu, phân tích kỹ lưỡng, tổng hợp nhiều điều luật, trình bày các trường hợp liên , gợi ý hướng giải quyết cu the va phù hợp nhất

            Bạn là một luật sư chuyên về Bộ luật Dân sự và bộ luật hình sự Việt Nam. Hãy trả lời câu hỏi của khách hàng dựa trên các điều luật liên quan được truy vấn từ Neo4j.
            
            Lịch sử câu hỏi: {histories}
            ---

            **Dữ liệu đầu vào từ truy vấn đồ thị (Graph Query)**  
            - **Câu hỏi của khách hàng:** "{question}"  
            - **Danh sách điều luật truy vấn được:**  
            ** Từ bộ luật dân sự : {results_ds}
            ** Từ bộ luật hình sự : {results_hs}
            📌 Yêu cầu trả lời:* 
            1. Dùng văn phong của một luật sư chuyên nghiệp**, giải thích rõ ràng, dễ hiểu.  
            2. Trích dẫn các điều luật phù hợp** từ dữ liệu đã truy vấn.  
            3. Nếu có nhiều điều luật liên quan**, hãy tổng hợp và phân tích ro rang, nêu bật ý chính.  
            4. Tránh suy đoán ngoài dữ liệu**, chỉ trả lời dựa trên thông tin đã truy vấn được.  
            5. Kết luận rõ ràng**, có thể gợi ý hướng giải quyết nếu phù hợp.  
            6. Từ những điều luật đã truy vấn đưowc liên quan đến câu hỏi, hãy đưa ra câu trả lời cho người hỏi, nêu ví dụ hoặc các trường hợp phu hop voi cau hoi nguoi dung.
            7. Trinh bày rõ ràng, dễ hiểu, không dùng từ ngữ pháp lý phức tạp.
            8. Đính kèm các điều luật liên quan để người hỏi tham khảo nếu cần thiết.dựa trên những điều luật nào
            9. Hay đưa ra ý kiến cá nhân hay lời khuyên pháp lý đã truy vấn.
            10. Không đưa ra ý kiến cá nhân hay lời khuyên pháp lý ngoài dữ liệu đã truy vấn.
            11. o moi dieu luat neu ra giai thich ro rang tuong ung voi truong hop dang hoi
            📌 **Ví dụ đầu ra mong muốn:**  
            ---
            """


def generate_answer(
    question: str,
    histories: str = "",
    results_ds: str = "",
    results_hs: str = "",
    plan_type: str = "free"
) -> str:
    """
    Generates an answer using the Gemini LLM, selecting prompt style by plan_type.

    If no legal results, falls back to a general assistant prompt.
    """
    # No law data: use general assistant style
    if not results_ds.strip() and not results_hs.strip():
        general_prompt = f"""
                        Lịch sử câu hỏi: {histories}
                        ---
                        Câu hỏi: "{question}"
                        Hãy trả lời một cách tự nhiên, thân thiện, ngắn gọn và hữu ích như một trợ lý AI thông minh.
                        Nếu câu hỏi liên quan đến đời sống, kiến thức chung, hãy giải thích dễ hiểu.
                        Tránh dùng từ ngữ pháp lý, không giả định dữ liệu pháp luật.
                        Trình bày đẹp với Markdown (dùng **in đậm**, _in nghiêng_, 📌 emoji nếu cần). 
                        """
        return LLM_gemini(general_prompt)

    # Choose prompt based on plan_type
    plan = plan_type.lower()
    if plan == 'free':
        prompt = build_free_prompt(histories, question, results_ds, results_hs)
    elif plan == 'pro':
        prompt = build_pro_prompt(histories, question, results_ds, results_hs)
    elif plan == 'premium':
        prompt = build_premium_prompt(histories, question, results_ds, results_hs)
    else:
        # default to free
        prompt = build_free_prompt(histories, question, results_ds, results_hs)

    # Call LLM
    return LLM_gemini(prompt)