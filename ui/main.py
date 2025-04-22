import gradio as gr
import requests

API_URL = "http://localhost:8001/chat"

EXAMPLES = [
    "Chồng của tôi đã bỏ nhà đi 15 năm mà không liên lạc với gia đình. Hiện tại, tôi không biết chồng của tôi đang ở đâu, làm gì, liệu có còn sống không. Vì vậy, tôi muốn hỏi trường hợp như chồng tôi đã được coi là mất tích hay chưa? Tài sản mà vợ chồng tôi đã có trước khi anh bỏ nhà đi sẽ được chia như thế nào? Xin cảm ơn!",
    "Nếu nam nữ không đăng ký kết hôn, sống chung với nhau như vợ chồng thì pháp luật có cho phép được hưởng tài sản thừa kế của nhau khi một người chết không? Có thể chứng minh việc chung sống như vợ chồng bằng cách nào để được Tòa án chấp nhận thưa Luật sư? Xin cảm ơn!",
    "Có những cách thanh lý tài sản cầm cố nào theo quy định pháp luật? Nếu trong trường hợp tài sản cầm cố phải thanh lý thì thứ tự ưu tiên thanh toán tiền thu được sau khi thanh lý tài sản cầm cố như thế nào? Xin cảm ơn!"
]


def send_message(message, history):
    # 1. Request to the API
    response = requests.post(API_URL, json={
        "question": message,
        "histories": history,
    })
    if response.status_code != 200:
        return "Có lỗi xảy ra khi gửi yêu cầu đến API."

    return response.json()["response"]


demo = gr.ChatInterface(fn=send_message, type="messages",
                        examples=EXAMPLES, title="Vietnamese Law Bot")
demo.launch()
