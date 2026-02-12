import pygame
import time
# For text box
import pygame_widgets
from pygame_widgets.textbox import TextBox

import app.request as request_module
from app.game_classes import *
import app.game_quizes as gq  # Import as module to maintain global variable references

#=============Global Variables==================
part1_payload = None
#part1_answers = []
part2_payload = None
part1_answers_cached = []

# Entering somewhere
can_enter_home = False
can_enter_wiseman = False
can_enter_exit_gate = False  # exit gate from training ground

# Player Information
player_name = ""
player_gender = None  # "male" / "female" 

# Current Game State
#state = PROFILE
state = OUTSIDE

# Initialize
pygame.init()

# Window
screen = pygame.display.set_mode((GAME_WIDTH,GAME_HEIGHT)) # fixed window size
pygame.display.set_caption("Welcome to PyGame!") # window header
font = pygame.font.SysFont('Arial', 32)

# Background Images
## Chapter 1
bg_img = pygame.image.load("images/background.png")  #.convert_alpha()
bg_img = pygame.transform.scale(bg_img, (GAME_WIDTH, GAME_HEIGHT))
#img = pygame.transform.scale(img, (img.get_width()*0.3, img.get_height()*0.3))
## Chapter 2
chapter2_bg = pygame.image.load("images/chapter2_bg.png")
chapter2_bg = pygame.transform.scale(chapter2_bg, (GAME_WIDTH, GAME_HEIGHT))

def print_output():
    print(textbox.getText())

'''
textbox = TextBox(screen, 100, 100, 500, 80, fontSize=50, #screen, x coordinate, y coordinate, width, height
                  borderColour=(0,0,0), textColour=(0,0,0), placeholderText="Type Something...",
                  onSubmit=print_output, radius=5, borderThickness=5) # onSubmit -> calls a function when enter button pressed; radius -> corner rounding;
'''

profile_name_box = TextBox(
    screen, 260, 155, 420, 45,
    fontSize=32,
    borderColour=WHITE,
    textColour=BLACK,
    boxColour=WHITE,
    placeholderText="Enter username...",
    radius=6,
    borderThickness=2,
)
profile_name_box.active = True

# Profile
## Username

## Gender
gender_options = ["male", "female"]
gender_selected_idx = 0  # default highlight
gender_rects = [
    pygame.Rect(250, 260, 20, 20),
    pygame.Rect(250, 310, 20, 20),
]

# Clock
clock = pygame.time.Clock()

# Invoking Main Player Instance
main_player = Player(x=GAME_WIDTH // 2, y=GAME_HEIGHT // 2, width=100, height=100, img_path="images/warrior/", speed=800)
fedora = Player(x=GAME_WIDTH - 400, y=GAME_HEIGHT - 200, width=100, height=100, img_path="images/fedora/", speed=80)
wiseman = Player(x=GAME_WIDTH - 400, y=GAME_HEIGHT - 200, width=100, height=100, img_path="images/wiseman/", speed=80)

#================ Structures ==========================

# Structures for Chapter I
home = Structure(GAME_WIDTH-650, GAME_HEIGHT-450, 200, 200, "images/house.png", "images/home_bg.png")
wiseman_tent = Structure(GAME_WIDTH - 400, GAME_HEIGHT - 200, 100, 100, "images/wiseman/west.png", "images/home_bg.png")
exit_gate1 = Structure(GAME_WIDTH - 260, GAME_HEIGHT - 250, 100, 100, "images/gate.png", "images/home_bg.png")

# Structures for Chapter II
portal1 = Structure(GAME_WIDTH - 660, GAME_HEIGHT - 500, 100, 100, "images/portal.png", "images/home_bg.png")
portal2 = Structure(GAME_WIDTH - 540, GAME_HEIGHT - 500, 100, 100, "images/home.png", "images/home_bg.png")
portal3 = Structure(GAME_WIDTH - 420, GAME_HEIGHT - 500, 100, 100, "images/heart.png", "images/home_bg.png")
#===============================================

def loading_screen(title: str):
    print("loading screen")

    screen.fill(BLACK)
    # TEXT
    font = pygame.font.SysFont('Arial', 32)
    text = font.render(f"{title}", True, WHITE)

    screen.blit(text, [300,300])

    pygame.display.flip()
    time.sleep(1)


#=========================Managing Locations===================================
def set_state(new_state, spawn_pos=None, title=None):
    global state
    state = new_state
    if spawn_pos is not None:
        main_player.rect.topleft = spawn_pos
    if title:
        loading_screen(title)

def render_state():
    '''
    Render/Draws the world
    '''
    if state == OUTSIDE:
        '''
        Chapter I : The Training Ground
        '''
        screen.blit(bg_img, (0, 0))
        home.draw(screen)
        wiseman_tent.draw(screen)

        exit_gate1.draw(screen)
        main_player.draw(screen)

    elif state == HOME:
        if gq.quiz_i < len(gq.quiz_questions_home):
            gq.draw_quiz_screen(screen, font, home.bg, gq.quiz_questions_home[gq.quiz_i], npc_name="Fedora")

            temp_main_player_img_home = pygame.transform.scale(main_player.img_down, (250, 250))
            temp_fedora_img_home = pygame.transform.scale(fedora.img_down, (200, 200))
            screen.blit(temp_main_player_img_home, (100, 360))
            screen.blit(temp_fedora_img_home, (500, 380))

    elif state == WISEMAN:
        '''
        print("IN RENDER WISEMAN")
        print(gq.quiz_questions_wiseman)
        print("-" * 50)
        '''
        if gq.quiz_i < len(gq.quiz_questions_wiseman):
            gq.draw_quiz_screen(screen, font, home.bg, gq.quiz_questions_wiseman[gq.quiz_i], npc_name="The Wise Man")

            temp_main_player_img_meeting = pygame.transform.scale(main_player.img_down, (250, 250))
            temp_wiseman_img_meeting = pygame.transform.scale(wiseman.img_down, (200, 200))
            screen.blit(temp_main_player_img_meeting, (100, 360))
            screen.blit(temp_wiseman_img_meeting, (500, 380))

    elif state == CHAPTER2:
        '''
        Chapter II : The Portals
        '''
        screen.blit(chapter2_bg, (0, 0))
        # Add player
        main_player.draw(screen)

        # Portals
        portal1.draw(screen)
        portal2.draw(screen)
        portal3.draw(screen)
        # Add any NPC or UI for chapter 2

    elif state == PROFILE:
        screen.fill((20, 20, 20))

        title = font.render("Create Your Profile", True, WHITE)
        screen.blit(title, (220, 80))

        # Username label
        label = font.render("Username:", True, WHITE)
        screen.blit(label, (120, 160))
        profile_name_box.draw()

        # Gender label
        g_label = font.render("Gender:", True, WHITE)
        screen.blit(g_label, (120, 240))

        # Draw radio options
        small_font = pygame.font.SysFont('Arial', 26)
        for i, opt in enumerate(gender_options):
            r = gender_rects[i]

            # outer circle/box
            pygame.draw.rect(screen, WHITE, r, 2)

            # filled if selected
            if i == gender_selected_idx:
                inner = r.inflate(-8, -8)
                pygame.draw.rect(screen, WHITE, inner)

            txt = small_font.render(opt, True, WHITE)
            screen.blit(txt, (r.x + 40, r.y - 5))

        hint = small_font.render("Enter = confirm • Click gender • Tab to focus textbox", True, (180,180,180))
        screen.blit(hint, (120, 520))

        print("TEXTBOX:", repr(profile_name_box.getText())) 

    else:
        pass

def update_outside_interactions():
    global can_enter_home, can_enter_wiseman, can_enter_exit_gate

    can_enter_home = main_player.rect.colliderect(home.rect)
    can_enter_wiseman = main_player.rect.colliderect(wiseman_tent.rect)
    can_enter_exit_gate = main_player.rect.colliderect(exit_gate1.rect)

#==========================Event Handlers================================
def handle_keydown_ch1(event):
    # E to enter
    if event.key == pygame.K_e:
        '''
        if can_enter_home:
            set_state(HOME, HOME_SPAWN, "Entering Home")
        '''
        if can_enter_home:
            global part1_payload, quiz_questions_home
            # Load questions - Part 1
            request_module.get_question_part1()

            gq.quiz_questions_home = request_module.quiz_questions_home
            # Reset counters
            gq.quiz_i = 0
            gq.quiz_done = False
            # Enter Home
            set_state(HOME, HOME_SPAWN, "Entering Home")
        elif can_enter_wiseman:
            global part2_payload, part1_answers_cached
            print("PART1 ANS CACHED")
            print(part1_answers_cached)
            print(type(part1_answers_cached[1]))
            print("-" * 50)

            # Load questions - Part 2
            part2_payload = request_module.get_question_part2(part1_answers_cached)
            gq.quiz_questions_wiseman = request_module.quiz_questions_wiseman
            print('MAIN QUIZ QUESTION WISEMAN')
            print(gq.quiz_questions_wiseman)
            # Reset counters
            gq.quiz_i = 0
            gq.quiz_done = False
            # Enter Wiseman
            set_state(WISEMAN, HOME_SPAWN, "Wise man")
        elif can_enter_exit_gate:
            set_state(CHAPTER2, (100, 300), "Chapter 2: The Portals")

def handle_profile_events(event):
    '''
    For handling profile events
    '''
    global gender_selected_idx, player_name, player_gender

    # mouse click -> select gender
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        mx, my = event.pos
        for i, r in enumerate(gender_rects):
            if r.collidepoint(mx, my):
                gender_selected_idx = i

    # Enter -> confirm
    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
        name = profile_name_box.getText().strip()
        if not name:
            print("Username required!")
            return

        player_name = name
        player_gender = gender_options[gender_selected_idx]
        print("Saved:", player_name, player_gender)

        set_state(OUTSIDE, OUTSIDE_SPAWN, "Chapter I : Finding Yourself")

#=================================================================

def in_quiz_mode():
    return state in (HOME, WISEMAN)

def get_active_quizzes():
    if state == HOME:
        return gq.quiz_questions_home
    if state == WISEMAN:
        return gq.quiz_questions_wiseman
    return None

# Main Loop
running = True
while running:
    dt = clock.tick(60) / 1000.0
    events = pygame.event.get()

    for event in events:
        # Quit
        if event.type == pygame.QUIT:
            running = False
            continue

        # Profile
        if state == PROFILE:
            pygame_widgets.update([event])   # feed event to textbox immediately
            handle_profile_events(event)
            continue

        if state in (HOME, WISEMAN):
            active = get_active_quizzes()
            if active is None:
                continue

            # Check if we should handle events first
            if gq.quiz_i < len(active):
                current_quiz = active[gq.quiz_i]

                if current_quiz.get("type") == "textinput":
                    pygame_widgets.update([event])

                if event.type == pygame.KEYDOWN:
                    print(state)
                    action = gq.handle_quiz_event(event, active)
                    print(f"handle_quiz_event returned: {action}")

                    if action == "quit":
                        state = OUTSIDE
                        gq.quiz_done = False
                        gq.quiz_i = 0

                    elif action == "next":
                        '''
                        print(f"Before quiz_next: quiz_i={gq.quiz_i}, len={len(active)}")
                        gq.quiz_next(active)
                        print(f"After quiz_next: quiz_i={gq.quiz_i}, quiz_done={gq.quiz_done}")
                        if gq.quiz_done:
                            print("All quiz results:", active)
                            state = OUTSIDE
                            gq.quiz_done = False
                            gq.quiz_i = 0
                        '''
                        gq.quiz_next(active)
                        if gq.quiz_done:
                            print("All quiz results:", active)
                            print(state)

                            if state == HOME:
                                # 2) After player answered all HOME quizzes
                                print("ui results to engine")
                                print(gq.quiz_questions_home)
                                part1_answers_cached = request_module.ui_results_to_engine_answers(gq.quiz_questions_home)
                                print(part1_answers_cached)
                                print("-" * 50)

                            elif state == WISEMAN:
                                # 4) After player answered all WISEMAN quizzes
                                part2_answers = request_module.ui_results_to_engine_answers(gq.quiz_questions_wiseman)
                                request_module.submit_part2_answers(part2_payload, part2_answers)

                            # exit quiz mode
                            state = OUTSIDE
                            gq.quiz_done = False
                            gq.quiz_i = 0
            else:
                # Quiz finished, exit to outside
                state = OUTSIDE
                gq.quiz_done = False
                gq.quiz_i = 0

            continue  # IMPORTANT: stop other key handlers while in quiz

        # Pressing Keys
        if event.type == pygame.KEYDOWN:

            print(f"{pygame.key.name(event.key)} has been pressed!")

            if state == OUTSIDE:
                '''
                Chapter I
                '''
                handle_keydown_ch1(event)
            else:
                # Chapter II
                if state == CHAPTER2:
                    # Quitting from Chapter II
                    if event.key == pygame.K_q:
                        set_state(OUTSIDE, OUTSIDE_SPAWN, "Returning Outside")

    # WIDGETS
    if state != PROFILE and state not in (HOME, WISEMAN):
        pygame_widgets.update(events)

    if state == OUTSIDE:
        main_player.move(dt, GAME_WIDTH, GAME_HEIGHT)
        update_outside_interactions()

    if state == CHAPTER2:
        main_player.move(dt, GAME_WIDTH, GAME_HEIGHT)

    # Render/Draw Location
    render_state()

    # FLIP THE DISPLAY
    pygame.display.flip()                             # refresh screen

# Step 4 - after loop is exited, quit pygame
pygame.quit()
