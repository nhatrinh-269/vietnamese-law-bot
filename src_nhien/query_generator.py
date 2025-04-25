from LLM_gemini import LLM_gemini


# Hàm sử dụng LLM để trích xuất từ khóa
def extract_keywords_with_llm(question):
    """
    Sử dụng LLM để trích xuất từ khóa từ câu hỏi và trả về dưới dạng JSON.
    """
    prompt = """
        Bạn là một chuyên gia pháp lý. Hãy phân tích câu hỏi sau và xác định các từ khóa chính liên quan đến Bộ luật dân sự và Bộ luật hình sự Việt Nam.

        Câu hỏi: "{question}"

         ##Yêu cầu:
        Hãy phân loại các từ khóa theo hai nhóm: Bộ luật dân sự và Bộ luật hình sự. 
        Ví dụ:          
        Bộ luật dân sự: tài sản, thừa kế, hợp đồng
        Bộ luật hình sự: tội phạm, hình phạt, trách nhiệm hình sự
        Hãy chắc chắn rằng bạn đã phân loại đúng các từ khóa theo từng bộ luật.
        Bạn không cần phải giải thích hay mô tả gì thêm. Chỉ cần trả về danh sách từ khóa theo định dạng JSON.
        Chỉ trả về danh sách từ khóa, không thêm giải thích hay mô tả gì khác ví dụ :  "```json", "```".
        Trích xuất các từ khóa pháp lý từ câu hỏi người dùng**  
        - Là các hành vi pháp lý (vd: chiếm hữu, thừa kế, sở hữu, khai báo, trộm cắp...)
        - Là khái niệm pháp lý hoặc thuật ngữ thường có trong văn bản luật
        - Từ khóa này có thể liên quan đến Bộ luật Dân sự hoặc Hình sự hoặc cả hai
        Trích xuất được nhiều từ khóa liên quan đến các điều luật trong bộ luật dân sự và bộ luật hình sự Việt Nam
        Trả về danh sách các từ khóa liên quan, mỗi từ khóa cách nhau bởi dấu phẩy.
        trả về danh sách từ khóa theo định dạng JSON như sau:   
        ##Output example:
        {
            "civil_keywords": ["từ khóa 1", "từ khóa 2"],
            "criminal_keywords": ["từ khóa 3", "từ khóa 4"]
        }
        
    Không được bao quanh bằng dấu ``` hoặc bất kỳ ký hiệu markdown nào. Không thêm giải thích, mô tả hoặc ghi chú..
    Nếu câu hỏi không liên quan đến luật pháp:
        Trả lời bình thường, không thực hiện trích xuất từ khóa.
        
        Ví dụ, nếu câu hỏi là "Trái đất quay quanh mặt trời như thế nào?"  không cần phân loại từ khóa và trả về json rỗng và không trả lời gì thêm.
        rả về JSON rỗng như sau:
        ##Output example:
        {}
    """
    # Thay thế {question} bằng câu hỏi thực tế
    prompt = prompt.replace("question", question)
    # Gọi LLM để lấy phản hồi
    response = LLM_gemini(prompt)
    # Làm sạch đầu ra để loại bỏ các ký tự không mong muốn
    cleaned_output = response.replace("```json", "").replace("```", "").strip()
    return cleaned_output


def generate_cypher_query_from_keywords(keywords):
    """
    Tạo truy vấn Cypher từ danh sách từ khóa đã phân loại theo Bộ luật Dân sự và Bộ luật Hình sự.
    """
    civil_keywords = keywords.get("civil_keywords", [])
    criminal_keywords = keywords.get("criminal_keywords", [])

    # Tạo điều kiện WHERE cho Bộ luật Dân sự
    civil_conditions = " OR ".join(
        [f'toLower(d.title) CONTAINS "{kw}" OR toLower(d.content) CONTAINS "{kw}"' for kw in civil_keywords]
    )
    civil_query = f"""
    MATCH (r:Root {{title: 'Luat Viet nam'}})-[:HAS_LAW]->(l:Law {{key: 'luat dan su'}})-[:HAS_CHAPTER]->(c:Chapter)-[:HAS_DIEU]->(d:Dieu)
    WHERE {civil_conditions}
    OPTIONAL MATCH (d)-[:REFERS_TO]->(ref:Dieu)
    RETURN d.dieu_number, d.title, d.content, collect(ref.dieu_number) AS referenced_articles
    """ if civil_conditions else ""

    # Tạo điều kiện WHERE cho Bộ luật Hình sự
    criminal_conditions = " OR ".join(
        [f'toLower(d.title) CONTAINS "{kw}" OR toLower(d.content) CONTAINS "{kw}"' for kw in criminal_keywords]
    )
    criminal_query = f"""
    MATCH (r:Root {{title: 'Luat Viet nam'}})-[:HAS_LAW]->(l:Law {{key: 'luat hinh su'}})-[:HAS_CHAPTER]->(c:Chapter)-[:HAS_DIEU]->(d:Dieu)
    WHERE {criminal_conditions}
    OPTIONAL MATCH (d)-[:REFERS_TO]->(ref:Dieu)
    RETURN d.dieu_number, d.title, d.content, collect(ref.dieu_number) AS referenced_articles
    """ if criminal_conditions else ""

    # Kết hợp các truy vấn bằng UNION
    return civil_query, criminal_query,
