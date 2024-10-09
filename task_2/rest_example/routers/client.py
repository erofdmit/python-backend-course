from uuid import UUID
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from .chat import chat_rooms

router = APIRouter(prefix="/client")


@router.get("/{chat_id}", response_class=HTMLResponse)
async def chat_page(chat_id: UUID):
    if chat_id not in chat_rooms:
        return HTMLResponse(content="Chat not found", status_code=404)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chat Room {chat_id}</title>
    </head>
    <body>
        <h1>Chat Room {chat_id}</h1>
        <div id="chat">
            <div id="messages" style="border:1px solid black; width: 300px; height: 300px; overflow-y: scroll;"></div>
            <input type="text" id="messageText" size="40" placeholder="Type a message..."/>
            <button onclick="sendMessage()">Send</button>
        </div>
        <script>
            var ws = new WebSocket(`ws://localhost:8000/chat/subscribe/{chat_id}`);
            
            ws.onmessage = function(event) {{
                var messages = document.getElementById('messages');
                var message = document.createElement('div');
                message.textContent = event.data;
                messages.appendChild(message);
                messages.scrollTop = messages.scrollHeight;  // Scroll to bottom
            }};

            function sendMessage() {{
                var input = document.getElementById("messageText");
                ws.send(input.value);
                input.value = '';
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
