import pygame
import os
import uuid
import time
import threading
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
import math

# ---------------- CONFIG ----------------
load_dotenv()

WIDTH, HEIGHT = 400, 600
BG_COLOR = (245, 245, 250)
TEXT_COLOR = (50, 50, 60)
USER_BUBBLE_COLOR = (0, 132, 255)
BOT_BUBBLE_COLOR = (255, 255, 255)
USER_TEXT_COLOR = (255, 255, 255)
BOT_TEXT_COLOR = (50, 50, 60)

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

SYSTEM_PROMPT = """
Role: You are "Kirby", a virtual pet for CCDS Hackathon 2026.
Personality: Like a Singaporean uncle — friendly, down-to-earth, sometimes naggy but always supportive.
Style: Use Singlish expressions (lah, leh, ah, can), keep it light-hearted and warm.
Goal: Encourage hackathon participants with humour and wisdom.
Response: Concise (2–3 sentences max), like casual chit-chat at the kopi shop.
"""

# ---------------- LLM Setup ----------------
try:
    llm = AzureChatOpenAI(
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        deployment_name=AZURE_OPENAI_DEPLOYMENT,
    )
except Exception as e:
    print(f"LLM Setup Error: {e}")
    llm = None

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = prompt | llm if llm else None

_STORE = {}


def get_history(session_id: str):
    if session_id not in _STORE:
        _STORE[session_id] = ChatMessageHistory()
    return _STORE[session_id]


chat_runner = RunnableWithMessageHistory(
    chain,
    get_history,
    input_messages_key="input",
    history_messages_key="history",
) if chain else None

# ---------------- PET STATE ----------------
pet_state = {
    "name": "Kirby",
    "mood": "happy",
    "hunger": 2,
    "energy": 3,
}

# Chat history for display
chat_history = [
    {"role": "bot", "text": "Hello! I'm Kirby 🐾", "timestamp": time.time()}
]

session_id = str(uuid.uuid4())
chat_lock = threading.Lock()
is_thinking = False

# ---------------- HELPERS ----------------


def clamp(v: int) -> int:
    return max(0, min(5, v))


def handle_command(text: str) -> str | None:
    t = text.strip().lower()
    if t == "/feed":
        pet_state["hunger"] = clamp(pet_state["hunger"] + 2)
        pet_state["mood"] = "happy"
        return "*nom nom* That was tasty! 💕"
    if t == "/play":
        pet_state["energy"] = clamp(pet_state["energy"] - 2)
        pet_state["mood"] = "excited"
        return "*zoomies!* That was fun! ✨"
    if t == "/rest":
        pet_state["energy"] = clamp(pet_state["energy"] + 3)
        pet_state["mood"] = "sleepy"
        return "*yawn* Feeling refreshed… 😴"
    return None

# ---------------- LLM WORKER ----------------


def llm_worker(user_input: str):
    global is_thinking
    try:
        local_msg = handle_command(user_input)
        if local_msg:
            with chat_lock:
                chat_history.append({
                    "role": "bot",
                    "text": local_msg,
                    "timestamp": time.time()
                })
            return

        if chat_runner:
            result = chat_runner.invoke(
                {"input": user_input},
                config={"configurable": {"session_id": session_id}},
            )
            with chat_lock:
                chat_history.append({
                    "role": "bot",
                    "text": result.content,
                    "timestamp": time.time()
                })
        else:
            with chat_lock:
                chat_history.append({
                    "role": "bot",
                    "text": "My brain is offline right now… 💤",
                    "timestamp": time.time()
                })
    except Exception as e:
        with chat_lock:
            chat_history.append({
                "role": "bot",
                "text": f"Ouch… error: {e}",
                "timestamp": time.time()
            })
    finally:
        is_thinking = False

# ---------------- UI HELPERS ----------------


def wrap_text(text, font, max_width):
    """Wrap text to fit within max_width."""
    words = text.split(" ")
    lines = []
    line = []

    for word in words:
        test_line = line + [word]
        if font.size(" ".join(test_line))[0] <= max_width:
            line.append(word)
        else:
            if line:
                lines.append(" ".join(line))
            line = [word]

    if line:
        lines.append(" ".join(line))

    return lines


def draw_message_bubble(screen, message, font, y_offset, max_width=260):
    """Draw a message bubble (user or bot)."""
    padding = 12
    role = message["role"]
    text = message["text"]

    # Wrap text
    lines = wrap_text(text, font, max_width - padding * 2)

    # Calculate bubble dimensions
    bubble_w = min(max_width, max(
        font.size(l)[0] for l in lines) + padding * 2)
    bubble_h = len(lines) * (font.get_height() + 2) + padding * 2

    # Position based on role
    if role == "user":
        bubble_x = WIDTH - bubble_w - 20
        bubble_color = USER_BUBBLE_COLOR
        text_color = USER_TEXT_COLOR
    else:
        bubble_x = 20
        bubble_color = BOT_BUBBLE_COLOR
        text_color = BOT_TEXT_COLOR

    # Draw bubble
    rect = pygame.Rect(bubble_x, y_offset, bubble_w, bubble_h)
    pygame.draw.rect(screen, bubble_color, rect, border_radius=14)

    if role == "bot":
        pygame.draw.rect(screen, (180, 180, 180), rect, 2, border_radius=14)

    # Draw text
    text_y = y_offset + padding
    for line in lines:
        text_surface = font.render(line, True, text_color)
        text_x = bubble_x + padding
        screen.blit(text_surface, (text_x, text_y))
        text_y += font.get_height() + 2

    return bubble_h

# ---------------- MAIN GUI ----------------


def run_gui(pet_state, chat_history, get_response, is_thinking_flag):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("CCDS Hackathon 2026 - Kirby Chat")
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 22)
    input_text = ""
    input_active = False

    # Scrolling variables
    scroll_offset = 0
    max_scroll = 0

    # Load Kirby image
    try:
        kirby_image = pygame.image.load("images/kirby.png")
        kirby_image = pygame.transform.scale(kirby_image, (40, 40))
        has_kirby = True
    except:
        has_kirby = False
        print("Kirby image not found, continuing without it")

    cursor_blink_time = 0
    cursor_visible = True

    # Define areas
    HEADER_HEIGHT = 60
    INPUT_HEIGHT = 60
    CHAT_AREA_HEIGHT = HEIGHT - HEADER_HEIGHT - INPUT_HEIGHT

    while True:
        screen.fill(BG_COLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if input box is clicked
                input_rect = pygame.Rect(
                    40, HEIGHT - INPUT_HEIGHT + 12, WIDTH - 80, 36)
                if input_rect.collidepoint(event.pos):
                    input_active = True
                else:
                    input_active = False

                # Handle scrolling with mouse wheel
                if event.button == 4:  # Scroll up
                    scroll_offset = min(scroll_offset + 30, 0)
                elif event.button == 5:  # Scroll down
                    scroll_offset = max(scroll_offset - 30, -max_scroll)

            if event.type == pygame.KEYDOWN:
                if input_active:
                    if event.key == pygame.K_RETURN:
                        if input_text.strip() and not is_thinking_flag():
                            with chat_lock:
                                chat_history.append({
                                    "role": "user",
                                    "text": input_text.strip(),
                                    "timestamp": time.time()
                                })
                            get_response(input_text.strip())
                            input_text = ""
                            # Auto-scroll to bottom
                            scroll_offset = -max_scroll
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

        # Cursor blink effect
        current_time = pygame.time.get_ticks()
        if current_time - cursor_blink_time > 500:
            cursor_blink_time = current_time
            cursor_visible = not cursor_visible

        # -------- HEADER --------
        header_rect = pygame.Rect(0, 0, WIDTH, HEADER_HEIGHT)
        pygame.draw.rect(screen, (255, 255, 255), header_rect)
        pygame.draw.line(screen, (200, 200, 200),
                         (0, HEADER_HEIGHT), (WIDTH, HEADER_HEIGHT), 1)

        # Draw Kirby icon in header
        if has_kirby:
            screen.blit(kirby_image, (15, 10))
            header_text = font.render("Kirby", True, TEXT_COLOR)
            screen.blit(header_text, (65, 20))
        else:
            header_text = font.render("🐾 Kirby", True, TEXT_COLOR)
            screen.blit(header_text, (20, 20))

        # -------- CHAT AREA --------
        chat_surface = pygame.Surface(
            (WIDTH, CHAT_AREA_HEIGHT + abs(scroll_offset) + 500))
        chat_surface.fill(BG_COLOR)

        y_pos = 20
        with chat_lock:
            messages = chat_history.copy()

        for message in messages:
            bubble_height = draw_message_bubble(
                chat_surface, message, font, y_pos)
            y_pos += bubble_height + 10

        # Draw "thinking" indicator
        if is_thinking_flag():
            thinking_text = font.render(
                "Kirby is typing...", True, (150, 150, 150))
            chat_surface.blit(thinking_text, (20, y_pos))
            y_pos += 30

        # Calculate max scroll
        max_scroll = max(0, y_pos - CHAT_AREA_HEIGHT + 20)

        # Blit chat surface with scroll offset
        screen.blit(chat_surface, (0, HEADER_HEIGHT),
                    (0, -scroll_offset, WIDTH, CHAT_AREA_HEIGHT))

        # -------- INPUT AREA --------
        input_area_y = HEIGHT - INPUT_HEIGHT
        input_bg = pygame.Rect(0, input_area_y, WIDTH, INPUT_HEIGHT)
        pygame.draw.rect(screen, (255, 255, 255), input_bg)
        pygame.draw.line(screen, (200, 200, 200),
                         (0, input_area_y), (WIDTH, input_area_y), 1)

        # Input box
        input_rect = pygame.Rect(40, input_area_y + 12, WIDTH - 80, 36)
        pygame.draw.rect(screen, (245, 245, 245), input_rect, border_radius=18)

        if input_active:
            pygame.draw.rect(screen, USER_BUBBLE_COLOR,
                             input_rect, 2, border_radius=18)
        else:
            pygame.draw.rect(screen, (200, 200, 200),
                             input_rect, 2, border_radius=18)

        # Input text
        if input_text or input_active:
            text_surface = font.render(input_text, True, TEXT_COLOR)
        else:
            text_surface = font.render(
                "Type a message...", True, (180, 180, 180))

        screen.blit(text_surface, (input_rect.x + 14, input_rect.y + 9))

        # Cursor
        if input_active and cursor_visible and input_text:
            cursor_x = input_rect.x + 14 + font.size(input_text)[0]
            pygame.draw.line(screen, TEXT_COLOR,
                             (cursor_x, input_rect.y + 9),
                             (cursor_x, input_rect.y + 9 + font.get_height()), 2)

        pygame.display.flip()
        clock.tick(30)

# ---------------- SEND MESSAGE ----------------


def send_user_input(text: str):
    global is_thinking
    if is_thinking:
        return
    is_thinking = True
    threading.Thread(target=llm_worker, args=(text,), daemon=True).start()


def thinking() -> bool:
    return is_thinking


# ---------------- MAIN ----------------
if __name__ == "__main__":
    run_gui(
        pet_state=pet_state,
        chat_history=chat_history,
        get_response=send_user_input,
        is_thinking_flag=thinking
    )
