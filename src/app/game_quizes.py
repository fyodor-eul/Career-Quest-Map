import json
import pygame
import pygame_widgets
from app.request import *
from pygame_widgets.textbox import TextBox

# Open Files
with open("data/options_catalog.json", "r", encoding="utf-8") as f:
    catalog = json.load(f)

FIELDS = catalog["fields_vocab"]  # e.g. Technology, Engineering, ...
COURSES = [c["name"] for c in catalog["courses_poly"]]  # course names
UNI_COURSES = [c["name"] for c in catalog["uni_courses"]]  # course names
CAREER = [c["name"] for c in catalog["careers_poly_work"]]  # course names

def draw_dialog_box(surface, rect, fill_color=(0,0,0), alpha=200, border_color=(255,255,255), border=3, radius=18):
    '''
    a small helper to draw a dialog box
    '''
    # draw translucent rounded box
    box = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(box, (*fill_color, alpha), box.get_rect(), border_radius=radius)
    surface.blit(box, (rect.x, rect.y))

    # border
    pygame.draw.rect(surface, border_color, rect, border, border_radius=radius)

def wrap_text(text, font, max_width):
    '''
    text wrapping
    '''
    words = text.split(" ")
    lines = []
    cur = ""

    for w in words:
        test = (cur + " " + w).strip()
        if font.size(test)[0] <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

# ----------------------------
# Quiz Engine State
# ----------------------------
quiz_i = 0            # current quiz index
quiz_done = False     # set True when finished

# For textinput widget (create once and reuse)
text_widget = None
text_widget_active_for_i = None

def ensure_text_widget(screen, box_rect):
    """
    Create a TextBox once (or reuse it).
    """
    global text_widget
    if text_widget is None:
        # put textbox inside dialog box area
        text_widget = TextBox(
            screen,
            box_rect.x + 20,
            box_rect.y + 190,
            box_rect.width - 40,
            45,
            fontSize=28,
            borderColour=(255, 255, 255),
            textColour=(0, 0, 0),
            boxColour=(255, 255, 255),
            radius=6,
            borderThickness=2,
        )
        text_widget.active = True
    return text_widget


def draw_quiz_screen(screen, font, bg, quiz, npc_name="NPC"):
    """
    Draw the current quiz based on quiz["type"].
    - Render background
    - Draw rectangle and dialog box
    - Show NPC name
    - Based on question type from `quiz`, draw multiple_choice, slider or textinput accordingly
    """

    # Background
    screen.blit(bg, (0, 0))

    # Draw Rect and dialog box
    box_rect = pygame.Rect(40, 50, 720, 330)
    draw_dialog_box(screen, box_rect, fill_color=(10, 10, 10), alpha=210, border_color=(255, 255, 255))

    # NPC name
    name_surf = font.render(npc_name + ":", True, (255, 255, 255))
    screen.blit(name_surf, (box_rect.x + 20, box_rect.y + 15))

    # Question text (wrapped)
    prompt_font = pygame.font.SysFont("Arial", 28)
    lines = wrap_text(quiz.get("question", ""), prompt_font, box_rect.width - 40)

    y = box_rect.y + 60
    for line in lines[:2]:
        screen.blit(prompt_font.render(line, True, (230, 230, 230)), (box_rect.x + 20, y))
        y += 32

    # Render based on question type
    qtype = quiz.get("type")
    if qtype == "multiple_choice":
        draw_multiple_choice(screen, box_rect, quiz)

        hint = pygame.font.SysFont("Arial", 24).render(
            "↑↓ choose • Enter confirm • 1-9 quick • Q exit", True, (180, 180, 180)
        )
        screen.blit(hint, (box_rect.x + 20, box_rect.bottom + 170))

    elif qtype == "slider":
        draw_slider(screen, box_rect, quiz)

        hint = pygame.font.SysFont("Arial", 24).render(
            "←→ change • Enter confirm • Q exit", True, (180, 180, 180)
        )
        screen.blit(hint, (box_rect.x + 20, box_rect.bottom + 170))

    elif qtype == "textinput":
        draw_textinput(screen, box_rect, quiz)

        hint = pygame.font.SysFont("Arial", 24).render(
            "Type answer • Enter confirm • Q exit", True, (180, 180, 180)
        )
        screen.blit(hint, (box_rect.x + 20, box_rect.bottom + 170))

    else:
        err = pygame.font.SysFont("Arial", 26).render(f"Unknown quiz type: {qtype}", True, (255, 100, 100))
        screen.blit(err, (box_rect.x + 20, box_rect.y + 150))


def draw_multiple_choice(screen, box_rect, quiz):
    opt_font = pygame.font.SysFont("Arial", 26)
    options = quiz.get("answers", [])
    selected_idx = int(quiz.get("user_choice_index", 0))
    opt_y = box_rect.y + 120

    for i, opt in enumerate(options):
        opt_rect = pygame.Rect(box_rect.x + 20, opt_y, box_rect.width - 40, 34)
        is_sel = (i == selected_idx)

        fill = (60, 60, 60) if is_sel else (30, 30, 30)
        pygame.draw.rect(screen, fill, opt_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), opt_rect, 2, border_radius=10)

        label = f"{i+1}. {opt}"
        color = (255, 255, 0) if is_sel else (255, 255, 255)
        screen.blit(opt_font.render(label, True, color), (opt_rect.x + 10, opt_rect.y + 5))

        opt_y += 50


def draw_slider(screen, box_rect, quiz):
    # slider values 0..select_count
    max_val = int(quiz.get("select_count", 10))
    val = int(quiz.get("user_choice_index", 0))
    val = max(0, min(max_val, val))

    # bar geometry
    bar_x = box_rect.x + 60
    bar_y = box_rect.y + 190
    bar_w = box_rect.width - 120
    bar_h = 10

    # bar
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_w, bar_h), border_radius=6)

    # knob position
    t = 0 if max_val == 0 else (val / max_val)
    knob_x = int(bar_x + t * bar_w)
    knob_y = bar_y + bar_h // 2

    pygame.draw.circle(screen, (255, 255, 0), (knob_x, knob_y), 12)
    pygame.draw.circle(screen, (255, 255, 255), (knob_x, knob_y), 12, 2)

    # label
    num_font = pygame.font.SysFont("Arial", 28)
    label = num_font.render(f"{val}/{max_val}", True, (230, 230, 230))
    screen.blit(label, (box_rect.x + 20, box_rect.y + 230))


def draw_textinput(screen, box_rect, quiz):
    """
    Draws a pygame_widgets TextBox inside the dialog box.
    quiz["user_input"] is used as the stored answer.
    """
    global text_widget, text_widget_active_for_i

    # Create or reuse widget
    tb = ensure_text_widget(screen, box_rect)

    # Placeholder display (pygame_widgets TextBox doesn't do placeholder nicely by default)
    # We'll show a faint placeholder ABOVE the textbox if empty.
    placeholder = quiz.get("placeholder", "")
    current = quiz.get("user_input", "")

    # Keep widget text synced (only when switching questions)
    # We don't want to overwrite what user is typing every frame.
    if text_widget_active_for_i != id(quiz):
        tb.setText(current)
        text_widget_active_for_i = id(quiz)
        tb.active = True

    # Draw textbox
    tb.draw()

    # draw placeholder hint if empty
    if (tb.getText() or "").strip() == "" and placeholder:
        ph_font = pygame.font.SysFont("Arial", 22)
        ph = ph_font.render(f"Example: {placeholder}", True, (180, 180, 180))
        screen.blit(ph, (box_rect.x + 20, box_rect.y + 160))


def handle_quiz_event(event, quizzes):
    """
    Update quizzes[quiz_i] based on input.
    Returns: "next", "quit", or None
    """
    global quiz_i, quiz_done, text_widget

    quiz = quizzes[quiz_i]
    qtype = quiz.get("type")

    if event.type == pygame.KEYDOWN:
        print("KEYDOWN:", pygame.key.name(event.key), "qtype:", qtype)


    # universal quit
    if event.type == pygame.KEYDOWN and event.key == pygame.K_q:
        return "quit"

    if qtype == "multiple_choice":
        if event.type == pygame.KEYDOWN:
            options = quiz.get("answers", [])
            n = len(options)
            if n == 0:
                return None

            if event.key == pygame.K_UP:
                quiz["user_choice_index"] = (quiz.get("user_choice_index", 0) - 1) % n
            elif event.key == pygame.K_DOWN:
                quiz["user_choice_index"] = (quiz.get("user_choice_index", 0) + 1) % n
            elif pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1
                if idx < n:
                    quiz["user_choice_index"] = idx
            elif event.key == pygame.K_RETURN:
                return "next"

    elif qtype == "slider":
        if event.type == pygame.KEYDOWN:
            max_val = int(quiz.get("select_count", 10))
            v = int(quiz.get("user_choice_index", 0))

            if event.key == pygame.K_LEFT:
                v = max(0, v - 1)
            elif event.key == pygame.K_RIGHT:
                v = min(max_val, v + 1)
            elif event.key == pygame.K_RETURN:
                return "next"

            quiz["user_choice_index"] = v

    elif qtype == "textinput":
        # Important: allow pygame_widgets to process typing events (do this in your main loop too)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            # Save text from widget into quiz dict
            if text_widget is not None:
                quiz["user_input"] = text_widget.getText()
            return "next"

    return None


def quiz_next(quizzes):
    global quiz_i, quiz_done, text_widget_active_for_i

    quiz_i += 1
    if quiz_i >= len(quizzes):
        quiz_done = True
        return  # <-- stop here, do NOT clamp quiz_i back

    text_widget_active_for_i = None

# Quiz
'''
quiz_questions_home = [
    {
        "type": "multiple_choice",
        "select_count": 4,
        "question": "What is your course of study",
        "answers": ["Engineering", "Design", "IT", "Business"],
        "user_choice_index": 0
    },
    {
        "type": "slider",
        "select_count": 10,
        "question": "How confident you are with our choice of major?",
        "user_choice_index": 0
    },
    {
        "type": "textinput",
        "question": "How do u manage with your subjects",
        "placeholder": "Manage time wisely",
        "user_input": "I try to connect theories with real-world scenarios"
    }
]

quiz_questions_wiseman = [
    {
        "type": "multiple_choice",
        "select_count": 4,
        "question": "What is your course of study WISEMAN",
        "answers": ["Engineering", "Design", "IT", "Business"],
        "user_choice_index": 0
    },
    {
        "type": "slider",
        "select_count": 10,
        "question": "How confident you are with our choice of major? WISEMAN",
        "user_choice_index": 0
    },
    {
        "type": "textinput",
        "question": "How do u manage with your subjects WISEMAN",
        "placeholder": "Manage time wisely",
        "user_input": "I try to connect theories with real-world scenarios"
    }
]
'''