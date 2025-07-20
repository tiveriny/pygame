import pygame
import sys
import random
import requests
import time
import uuid
import datetime
import threading

# Инициализация Pygame
pygame.init()

## Константы
WINDOW_SIZE = 720  # Уменьшаем размер окна с 800 до 720
CELL_SIZE = 30  # Уменьшаем размер клетки с 35 до 30
GRID_WIDTH = 14
GRID_HEIGHT = 15
MARGIN_X = (WINDOW_SIZE - GRID_WIDTH * CELL_SIZE) // 2
MARGIN_Y = (WINDOW_SIZE - GRID_HEIGHT * CELL_SIZE) // 2 - 10  # Смещаем поле немного выше

# Добавим константы для размера фишки в меню и количества фишек в ряду
MENU_SHIP_SIZE = 18  # Уменьшаем размер фишки в меню с 20 до 18
SHIPS_PER_ROW = 20  # Увеличиваем количество фишек в ряду с 18 до 20
MENU_SPACING = 3    # Уменьшаем расстояние между фишками с 4 до 3

# Константы для позиционирования меню
MENU_TOP_Y = 5  # Верхняя позиция меню для первого игрока
MENU_BOTTOM_Y = WINDOW_SIZE - 100  # Нижняя позиция меню для второго игрока
MENU_OFFSET_X = 100  # Уменьшаем смещение меню вправо с 150 до 100

# Константы для кнопки случайной расстановки
RANDOM_BUTTON_WIDTH = 100  # Уменьшаем ширину кнопки со 120 до 100
RANDOM_BUTTON_HEIGHT = 25  # Уменьшаем высоту кнопки с 30 до 25
RANDOM_BUTTON_X = 10  
RANDOM_BUTTON_Y = WINDOW_SIZE // 2 - RANDOM_BUTTON_HEIGHT // 2

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (160, 160, 160)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
LIGHT_BLUE = (173, 216, 230)
LIGHT_RED = (255, 182, 193)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
# --- УТИЛИТЫ ---

def find_neighbors(board, x, y, ship_type=None, player=None):
    neighbors = []
    for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        nx, ny = x+dx, y+dy
        if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
            neighbor = board[nx][ny]
            if neighbor and (ship_type is None or neighbor.type == ship_type) and (player is None or neighbor.player == player):
                neighbors.append(neighbor)
    return neighbors

class Ship:
    def __init__(self, name, player, ship_type):
        self.name = name
        self.player = player
        self.type = ship_type
        self.position = None
        self.hidden = True
        self.set_attributes()

    def set_attributes(self):
        # Dictionary mapping ship types to their attributes
        ship_attributes = {
            'Ст': {'movement_range': 1, 'rating': 1, 'combine_with': {'Ст', 'Тр'}, 'color': (0, 255, 0)},        # Green
            'Тр': {'movement_range': 1, 'rating': 2, 'combine_with': {'Тр', 'Ст'}, 'color': (0, 255, 0)},        # Green
            'Тк': {'movement_range': 2, 'rating': 3, 'combine_with': {'Тр', 'Тк'}, 'color': (0, 255, 0)},        # Green
            'Пл': {'movement_range': 1, 'rating': 4, 'combine_with': {'Пл'}, 'color': (160, 32, 240)},           # Purple
            'КРПЛ': {'movement_range': 1, 'rating': 5, 'combine_with': {'КРПЛ', 'Тк'}, 'color': (139, 69, 19)},  # Brown
            'Ф': {'movement_range': 1, 'rating': 3, 'combine_with': {'Ф', 'Эс'}, 'color': (0, 255, 0)},          # Green
            'Эс': {'movement_range': 1, 'rating': 4, 'combine_with': {'Эс', 'Ф', 'Л'}, 'color': (0, 0, 255)},    # Blue
            'Л': {'movement_range': 1, 'rating': 5, 'combine_with': {'Л', 'Эс'}, 'color': (0, 0, 255)},          # Blue
            'Кр': {'movement_range': 1, 'rating': 6, 'combine_with': {'Кр', 'Л', 'БДК'}, 'color': (255, 0, 0)}, # red
            'БДК': {'movement_range': 1, 'rating': 7, 'combine_with': {'БДК', 'Л', 'Эс'}, 'color': (255, 0, 0)},# red
            'А': {'movement_range': 1, 'rating': 8, 'combine_with': {'А', 'Кр', 'БДК'}, 'color': (255, 0, 0)}, # red
            'ВМБ': {'movement_range': 0, 'rating': 0, 'combine_with': set(), 'color': (0, 0, 0)},               # Black
            'СМ': {'movement_range': 0, 'rating': 0, 'combine_with': set(), 'color': (0, 0, 255)},             # Gray - Mine
            'АБ': {'movement_range': 1, 'rating': 0, 'combine_with': set(), 'color': (128, 128, 128)},                 # Red - Atomic Bomb
            'М': {'movement_range': 1, 'rating': 0, 'combine_with': set(), 'color': (0, 0, 255)},            # Light Gray - Regular Mine
            'С': {'movement_range': 1, 'rating': 0, 'combine_with': set(), 'color': (255, 0, 0)},               # Gold - Airplane
            'Т': {'movement_range': 1, 'rating': 0, 'combine_with': set(), 'color': (0, 255, 0)},                # Red-Orange - Torpedo
            'Тн': {'movement_range': 1, 'rating': 0, 'combine_with': set(), 'color': (255, 0, 0)}            # Tan - Tanker
        }
        attributes = ship_attributes.get(self.type, None)
        if attributes:
            self.movement_range = attributes['movement_range']
            self.rating = attributes['rating']
            self.combine_with = attributes['combine_with']
            self.color = attributes['color']
        else:
            # Default attributes for unknown ship types
            self.movement_range = 1
            self.rating = 1
            self.combine_with = set()
            self.color = (128, 128, 128)  # Gray

    def draw(self, screen, rect, current_player=None):
        if self.hidden:
            pygame.draw.rect(screen, GRAY, rect)
            return
        else:
            # Use the ship's specific color
            pygame.draw.rect(screen, self.color, rect)
            # Display the ship type abbreviation
            font = pygame.font.Font(None, 21)
            text = font.render(self.type, True, WHITE)
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)

class Game:
    def __init__(self, online_session=None, my_login=None, opponent_login=None):
        info = pygame.display.Info()
        window_size = min(WINDOW_SIZE, info.current_h - 60, info.current_w - 40)
        self.scale_factor = window_size / WINDOW_SIZE
        self.cell_size = int(CELL_SIZE * self.scale_factor)
        self.margin_x = int((window_size - GRID_WIDTH * self.cell_size) // 2)
        self.margin_y = int((window_size - GRID_HEIGHT * self.cell_size) // 2 - 10 * self.scale_factor)
        self.screen = pygame.display.set_mode((window_size, window_size))
        pygame.display.set_caption("Морская игра")
        self.board = [[None for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
        self.current_player = 1
        self.selected_ship = None
        self.player1_ships, self.player2_ships = [], []
        self.captured_ships_player1, self.captured_ships_player2 = [], []
        self.unplaced_ships_player1, self.unplaced_ships_player2 = [], []
        self.phase = 'setup'
        self.highlighted_cells, self.attackable_enemies = [], []
        self.waiting_for_spacebar = False
        self.combat_info = None
        self.previous_positions = {}
        self.last_cell_clicked, self.last_click_time = None, 0
        self.setup_complete, self.setup_message = False, None
        self.battle_active = False
        self.battle_turn_player = self.battle_attacker = self.battle_defender = None
        self.attacking_ships, self.defending_ships = [], []
        self.attacking_passed = self.defending_passed = False
        self.player_has_added_ships = False
        self.tr_additional_move = False
        self.initialize_ships()
        button_width = int(RANDOM_BUTTON_WIDTH * self.scale_factor)
        button_height = int(RANDOM_BUTTON_HEIGHT * self.scale_factor)
        button_x = int(RANDOM_BUTTON_X * self.scale_factor)
        button_y = int(window_size // 2 - button_height // 2)
        self.random_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        self.online_session = online_session
        self.my_login = my_login
        self.opponent_login = opponent_login
        # Таймеры
        self.setup_time = {1: 15*60, 2: 15*60}  # 15 минут на расстановку
        self.total_time = {1: 15*60, 2: 15*60}  # 15 минут общего времени
        self.move_time = 30  # 30 секунд на ход
        self.current_move_timer = self.move_time
        self.last_tick = time.time()
        self.pauses = {1: {"long": 1, "short": 1}, 2: {"long": 1, "short": 1}}
        self.pause_active = False
        self.pause_type = None
        self.pause_owner = None
        self.pause_end_time = None
        self.status_message = None

    def initialize_ships(self):
        # Только по 5 крейсеров у каждого игрока
        types = ["БДК","БДК","Кр", "Кр",  "Кр", "Кр", "Кр", "Кр","А", "С", "Тн","Л", "Л","Эс", "Эс",  "Эс", "Эс",  "Эс", "Эс", "М", "М", "М", "М",  "М", "М","СМ","Ф", "Ф", "Ф", "Ф", "Ф", "Ф",   "Тк", "Тк", "Тк", "Тк", "Тк", "Тк","Т", "Т", "Т", "Т", "Т", "Т", "Тр", "Тр", "Тр", "Тр", "Тр", "Тр",  "Ст", "Ст", "Ст", "Ст", "Ст", "Ст", "Пл","КРПЛ","АБ","ВМБ", "ВМБ"]

        for i, ship_type in enumerate(types):
            ship1 = Ship(f"Корабль_{i+1}_Игрок1", 1, ship_type)
            ship2 = Ship(f"Корабль_{i+1}_Игрок2", 2, ship_type)
            ship1.position = self.get_menu_position(i, 1)
            ship2.position = self.get_menu_position(i, 2)
            ship1.hidden = ship2.hidden = False
            self.unplaced_ships_player1.append(ship1)
            self.unplaced_ships_player2.append(ship2)

    def get_cell_from_mouse(self, pos):
        x, y = pos
        if self.margin_x <= x <= self.margin_x + GRID_WIDTH * self.cell_size and self.margin_y <= y <= self.margin_y + GRID_HEIGHT * self.cell_size:
            cell_x = (x - self.margin_x) // self.cell_size
            cell_y = (y - self.margin_y) // self.cell_size
            # Для игрока 2 инвертируем Y
            cell_x, cell_y = self.inverse_transform_coords(cell_x, cell_y)
            return (cell_x, cell_y)
        return None

    def serialize_ships(self, ships):
        # Сохраняем только тип, позицию и принадлежность
        return [
            {"type": ship.type, "position": ship.position, "player": ship.player}
            for ship in ships
        ]

    def deserialize_ships(self, ships_data):
        ships = []
        for data in ships_data:
            ship = Ship(f"{data['type']}_{data['player']}", data['player'], data['type'])
            ship.position = tuple(data['position']) if data['position'] else None
            ship.hidden = False
            ships.append(ship)
        return ships

    def save_setup_to_firebase(self):
        if not self.online_session:
            return
        # Сохраняем свою расстановку
        setup_key = f"setup_{self.my_login}"
        ships_data = self.serialize_ships(self.player1_ships if self.current_player == 1 else self.player2_ships)
        self.online_session.update_state({setup_key: ships_data})

    def wait_for_opponent_setup(self):
        if not self.online_session:
            return
        opponent_key = f"setup_{self.opponent_login}"
        self.status_message = "Ожидание соперника..."
        self.draw_board()
        while True:
            state = self.online_session.get_state()
            if state and opponent_key in state:
                # Загружаем расстановку соперника
                ships_data = state[opponent_key]
                ships = self.deserialize_ships(ships_data)
                if self.current_player == 1:
                    self.player2_ships = ships
                else:
                    self.player1_ships = ships
                break
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
            time.sleep(1)
            self.draw_board()

    def serialize_game_state(self):
        # Сохраняем всё поле, чей ход, статус
        return {
            "player1_ships": self.serialize_ships(self.player1_ships),
            "player2_ships": self.serialize_ships(self.player2_ships),
            "current_player": self.current_player,
            "phase": self.phase,
            "winner": getattr(self, 'winner', None)
        }

    def deserialize_game_state(self, state):
        self.player1_ships = self.deserialize_ships(state.get("player1_ships", []))
        self.player2_ships = self.deserialize_ships(state.get("player2_ships", []))
        self.current_player = state.get("current_player", 1)
        self.phase = state.get("phase", 'game')
        if state.get("winner"):
            self.winner = state["winner"]
        else:
            self.winner = None
        # Перестроить board
        self.board = [[None for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)]
        for ship in self.player1_ships + self.player2_ships:
            if ship.position:
                x, y = ship.position
                self.board[x][y] = ship

    def sync_to_firebase(self):
        if self.online_session:
            self.online_session.update_state(self.serialize_game_state())

    def sync_from_firebase(self):
        if self.online_session:
            state = self.online_session.get_state()
            if state:
                self.deserialize_game_state(state)

    def run(self):
        clock = pygame.time.Clock()
        running = True
        self.status_message = None
        last_state = None
        while running:
            self.tick_timers()
            # --- ONLINE SYNC ---
            if self.online_session:
                # Синхронизация паузы
                state = self.online_session.get_state()
                if state and "pause" in state:
                    pause = state["pause"]
                    if pause.get("active"):
                        self.pause_active = True
                        self.pause_type = pause.get("type")
                        self.pause_owner = pause.get("owner")
                        self.pause_end_time = pause.get("end")
                    else:
                        self.pause_active = False
                        self.pause_type = None
                        self.pause_owner = None
                        self.pause_end_time = None
                # Если не наш ход — только слушаем Firebase
                if self.phase == 'game' and self.current_player != (1 if self.my_login == self.online_session.player_login else 2):
                    self.status_message = "Ход соперника..."
                    self.draw_board()
                    self.sync_from_firebase()
                    # Проверка на победу
                    if hasattr(self, 'winner') and self.winner:
                        self.game_over(self.winner)
                        return
                    time.sleep(1)
                    continue
            # --- END ONLINE SYNC ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if self.phase == 'setup':
                    self.handle_setup_event(event)
                else:
                    # Только если наш ход
                    if not self.online_session or self.current_player == (1 if self.my_login == self.online_session.player_login else 2):
                        self.handle_game_event(event)
            self.draw_board()
            # --- ONLINE SETUP SYNC ---
            if self.phase == 'setup' and self.setup_complete and self.online_session:
                self.save_setup_to_firebase()
                self.wait_for_opponent_setup()
                # После обмена расстановками — старт игры
                self.phase = 'game'
                self.current_player = 1
                self.setup_complete = False
                self.setup_message = None
                self.update_ship_visibility()
                self.sync_to_firebase()
            # --- END ONLINE SETUP SYNC ---
            # --- ONLINE GAME SYNC ---
            if self.phase == 'game' and self.online_session:
                # Если был ход — синхронизируем
                if last_state != self.serialize_game_state():
                    self.sync_to_firebase()
                    last_state = self.serialize_game_state()
            # --- END ONLINE GAME SYNC ---
            clock.tick(60)
        pygame.quit()

    def handle_setup_event(self, event):        
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos
            
            # Проверяем нажатие на кнопку случайной расстановки
            if self.random_button_rect.collidepoint(pos):
                self.place_ships_randomly()
                return
                
            # Проверяем попадание в корабль для размещения
            if self.current_player == 1:
                # Сначала проверяем корабли на доске
                for ship in self.player1_ships:
                    cell = self.get_cell_from_mouse(pos)
                    if cell and self.board[cell[0]][cell[1]] == ship:
                        self.selected_ship = ship
                        self.offset_x = cell[0] * self.cell_size + self.margin_x - pos[0]
                        self.offset_y = cell[1] * self.cell_size + self.margin_y - pos[1]
                        break
                # Если не нашли на доске, проверяем неразмещенные корабли
                if not self.selected_ship:
                    menu_ship_size = int(MENU_SHIP_SIZE * self.scale_factor)
                    for ship in self.unplaced_ships_player1:
                        rect = pygame.Rect(ship.position[0], ship.position[1],
                                           menu_ship_size, menu_ship_size)
                        if rect.collidepoint(pos):
                            self.selected_ship = ship
                            self.offset_x = ship.position[0] - pos[0]
                            self.offset_y = ship.position[1] - pos[1]
                            break

            elif self.current_player == 2:
                # Сначала проверяем корабли на доске
                for ship in self.player2_ships:
                    cell = self.get_cell_from_mouse(pos)
                    if cell and self.board[cell[0]][cell[1]] == ship:
                        self.selected_ship = ship
                        self.offset_x = cell[0] * self.cell_size + self.margin_x - pos[0]
                        self.offset_y = cell[1] * self.cell_size + self.margin_y - pos[1]
                        break
                # Если не нашли на доске, проверяем неразмещенные корабли
                if not self.selected_ship:
                    menu_ship_size = int(MENU_SHIP_SIZE * self.scale_factor)
                    for ship in self.unplaced_ships_player2:
                        rect = pygame.Rect(ship.position[0], ship.position[1],
                                           menu_ship_size, menu_ship_size)
                        if rect.collidepoint(pos):
                            self.selected_ship = ship
                            self.offset_x = ship.position[0] - pos[0]
                            self.offset_y = ship.position[1] - pos[1]
                            break

        elif event.type == pygame.MOUSEMOTION:
            if self.selected_ship:
                pos = event.pos
                if self.selected_ship in (self.unplaced_ships_player1 if self.current_player == 1 else self.unplaced_ships_player2):
                    self.selected_ship.position = (pos[0] + self.offset_x,
                                                   pos[1] + self.offset_y)
                else:
                    # Для кораблей на доске обновляем их позицию
                    cell = self.get_cell_from_mouse(pos)
                    if cell:
                        x, y = cell
                        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                            if self.board[x][y] is None and ((self.current_player == 1 and y < 5) or (self.current_player == 2 and y >= GRID_HEIGHT - 5)):
                                # Очищаем старую позицию
                                old_pos = self.selected_ship.position
                                if isinstance(old_pos, tuple) and len(old_pos) == 2:
                                    self.board[old_pos[0]][old_pos[1]] = None
                                # Обновляем позицию
                                self.selected_ship.position = (x, y)
                                self.board[x][y] = self.selected_ship

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.selected_ship:
                pos = event.pos
                cell = self.get_cell_from_mouse(pos)
                if cell:
                    x, y = cell
                    # Проверяем границы доски перед проверкой ячейки
                    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                        # Проверяем, что ячейка свободна и находится в разрешённом секторе
                        if self.board[x][y] is None and ((self.current_player == 1 and y < 5) or (self.current_player == 2 and y >= GRID_HEIGHT - 5)):
                            # Если корабль был на доске, очищаем его старую позицию
                            if self.selected_ship in (self.player1_ships if self.current_player == 1 else self.player2_ships):
                                old_pos = self.selected_ship.position
                                if isinstance(old_pos, tuple) and len(old_pos) == 2:
                                    self.board[old_pos[0]][old_pos[1]] = None
                            else:
                                # Если корабль был неразмещенным, добавляем его в список размещенных
                                if self.current_player == 1:
                                    self.player1_ships.append(self.selected_ship)
                                    self.unplaced_ships_player1.remove(self.selected_ship)
                                else:
                                    self.player2_ships.append(self.selected_ship)
                                    self.unplaced_ships_player2.remove(self.selected_ship)
                            
                            self.board[x][y] = self.selected_ship
                            self.selected_ship.position = (x, y)
                            
                            # Проверяем, все ли корабли размещены
                            if self.current_player == 1 and not self.unplaced_ships_player1:
                                self.setup_complete = True
                                self.setup_message = "Нажмите ПРОБЕЛ, чтобы передать ход другому игроку"
                            elif self.current_player == 2 and not self.unplaced_ships_player2:
                                self.setup_complete = True
                                self.setup_message = "Нажмите ПРОБЕЛ, чтобы начать игру"
                        else:
                            # Возвращаем корабль на его текущую позицию в меню
                            if self.selected_ship in (self.unplaced_ships_player1 if self.current_player == 1 else self.unplaced_ships_player2):
                                idx = (self.unplaced_ships_player1 if self.current_player == 1 else self.unplaced_ships_player2).index(self.selected_ship)
                                
                                # Масштабированные значения
                                menu_ship_size = int(MENU_SHIP_SIZE * self.scale_factor)
                                menu_spacing = int(MENU_SPACING * self.scale_factor)
                                menu_top_y = int(MENU_TOP_Y * self.scale_factor)
                                menu_bottom_y = self.screen.get_height() - int(100 * self.scale_factor)
                                
                                row = idx // SHIPS_PER_ROW
                                col = idx % SHIPS_PER_ROW
                                
                                # Рассчитываем общую ширину меню
                                menu_width = SHIPS_PER_ROW * (menu_ship_size + menu_spacing)
                                menu_offset_x = int(MENU_OFFSET_X * self.scale_factor)
                                menu_start_x = ((self.screen.get_width() - menu_width) // 2) + menu_offset_x
                                
                                if self.current_player == 1:
                                    self.selected_ship.position = (menu_start_x + col * (menu_ship_size + menu_spacing), 
                                                                  menu_top_y + row * (menu_ship_size + menu_spacing))
                                else:
                                    self.selected_ship.position = (menu_start_x + col * (menu_ship_size + menu_spacing), 
                                                                  menu_bottom_y + row * (menu_ship_size + menu_spacing))
                            else:
                                # Если корабль был на доске, возвращаем его на прежнюю позицию
                                old_pos = self.selected_ship.position
                                if isinstance(old_pos, tuple) and len(old_pos) == 2:
                                    self.board[old_pos[0]][old_pos[1]] = self.selected_ship
                else:
                    # Возвращаем корабль на место в меню
                    if self.selected_ship in (self.unplaced_ships_player1 if self.current_player == 1 else self.unplaced_ships_player2):
                        idx = (self.unplaced_ships_player1 if self.current_player == 1 else self.unplaced_ships_player2).index(self.selected_ship)
                        
                        # Масштабированные значения
                        menu_ship_size = int(MENU_SHIP_SIZE * self.scale_factor)
                        menu_spacing = int(MENU_SPACING * self.scale_factor)
                        menu_top_y = int(MENU_TOP_Y * self.scale_factor)
                        menu_bottom_y = self.screen.get_height() - int(100 * self.scale_factor)
                        
                        row = idx // SHIPS_PER_ROW
                        col = idx % SHIPS_PER_ROW
                        
                        # Рассчитываем общую ширину меню
                        menu_width = SHIPS_PER_ROW * (menu_ship_size + menu_spacing)
                        menu_offset_x = int(MENU_OFFSET_X * self.scale_factor)
                        menu_start_x = ((self.screen.get_width() - menu_width) // 2) + menu_offset_x
                        
                        if self.current_player == 1:
                            self.selected_ship.position = (menu_start_x + col * (menu_ship_size + menu_spacing), 
                                                          menu_top_y + row * (menu_ship_size + menu_spacing))
                        else:
                            self.selected_ship.position = (menu_start_x + col * (menu_ship_size + menu_spacing), 
                                                          menu_bottom_y + row * (menu_ship_size + menu_spacing))
                    else:
                        # Если корабль был на доске, возвращаем его на прежнюю позицию
                        old_pos = self.selected_ship.position
                        if isinstance(old_pos, tuple) and len(old_pos) == 2:
                            self.board[old_pos[0]][old_pos[1]] = self.selected_ship
                self.selected_ship = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self.setup_complete:
                if self.current_player == 1 and not self.unplaced_ships_player1:
                    self.current_player = 2
                    self.setup_complete = False
                    self.setup_message = None
                    self.update_ship_visibility()
                elif self.current_player == 2 and not self.unplaced_ships_player2:
                    self.phase = 'game'
                    self.current_player = 1
                    self.setup_complete = False
                    self.setup_message = None
                    self.update_ship_visibility()

    def handle_game_event(self, event):
        if self.battle_active:
            self.handle_battle_event(event)
            return
            
        # At the start of a player's turn, check if they can make any moves
        if not self.selected_ship and not self.waiting_for_spacebar:
            if not self.can_player_make_move(self.current_player):
                self.game_over(winner=3 - self.current_player)
                return
                
        if self.waiting_for_spacebar:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                # Special case for airplane attack
                if self.selected_ship and self.selected_ship.type == 'С':
                    x, y = self.selected_ship.position
                    # First check for atomic bombs in the attack line
                    if self.current_player == 1:  # Player 1 moves up
                        for dy in range(0, 6):  # Include the airplane's position (dy=0)
                            ny = y + dy
                            if 0 <= ny < GRID_HEIGHT:
                                target = self.board[x][ny]
                                if target and target.type == 'АБ':  # Found atomic bomb
                                    # Show all ships in the explosion area
                                    for dx in range(-2, 3):
                                        for dy2 in range(-2, 3):
                                            nx = x + dx
                                            ny2 = ny + dy2
                                            if 0 <= nx < GRID_WIDTH and 0 <= ny2 < GRID_HEIGHT:
                                                affected = self.board[nx][ny2]
                                                if affected:
                                                    affected.hidden = False
                                    # Remove the airplane first
                                    self.remove_ship(self.selected_ship)
                                    # Then remove all ships in the explosion area
                                    for dx in range(-4, 5):
                                        for dy2 in range(-4, 5):
                                            nx = x + dx
                                            ny2 = ny + dy2
                                            if 0 <= nx < GRID_WIDTH and 0 <= ny2 < GRID_HEIGHT:
                                                affected = self.board[nx][ny2]
                                                if affected:
                                                    self.remove_ship(affected)
                                    return  # Exit after atomic bomb explosion
                    else:  # Player 2 moves down
                        for dy in range(0, -6, -1):  # Include the airplane's position (dy=0)
                            ny = y + dy
                            if 0 <= ny < GRID_HEIGHT:
                                target = self.board[x][ny]
                                if target and target.type == 'АБ':  # Found atomic bomb
                                    # Show all ships in the explosion area
                                    for dx in range(-2, 3):
                                        for dy2 in range(-2, 3):
                                            nx = x + dx
                                            ny2 = ny + dy2
                                            if 0 <= nx < GRID_WIDTH and 0 <= ny2 < GRID_HEIGHT:
                                                affected = self.board[nx][ny2]
                                                if affected:
                                                    affected.hidden = False
                                    # Remove the airplane first
                                    self.remove_ship(self.selected_ship)
                                    # Then remove all ships in the explosion area
                                    for dx in range(-4, 5):
                                        for dy2 in range(-4, 5):
                                            nx = x + dx
                                            ny2 = ny + dy2
                                            if 0 <= nx < GRID_WIDTH and 0 <= ny2 < GRID_HEIGHT:
                                                affected = self.board[nx][ny2]
                                                if affected:
                                                    self.remove_ship(affected)
                                    return  # Exit after atomic bomb explosion

                    # If no atomic bombs found, proceed with regular airplane attack
                    if self.current_player == 1:  # Player 1 moves up
                        for dy in range(0, 6):  # Include the airplane's position (dy=0)
                            ny = y + dy
                            if 0 <= ny < GRID_HEIGHT:
                                target = self.board[x][ny]
                                if target:
                                    self.remove_ship(target)
                    else:  # Player 2 moves down
                        for dy in range(0, -6, -1):  # Include the airplane's position (dy=0)
                            ny = y + dy
                            if 0 <= ny < GRID_HEIGHT:
                                target = self.board[x][ny]
                                if target:
                                    self.remove_ship(target)
                    # Set battle_attacker for cleanup
                    self.battle_attacker = self.current_player
                # Special case for torpedo attack
                elif self.selected_ship and self.selected_ship.type == 'Т':
                    # Find the torpedo boat behind the torpedo
                    torpedo_x, torpedo_y = self.selected_ship.position
                    torpedo_boat = None
                    
                    if self.current_player == 1:  # Player 1 moves up
                        if torpedo_y - 1 >= 0:  # Торпедный катер должен быть над торпедой
                            tk = self.board[torpedo_x][torpedo_y - 1]
                            if tk and tk.type == 'Тк' and tk.player == self.current_player:
                                torpedo_boat = tk
                    else:  # Player 2 moves down
                        if torpedo_y + 1 < GRID_HEIGHT:  # Торпедный катер должен быть под торпедой
                            tk = self.board[torpedo_x][torpedo_y + 1]
                            if tk and tk.type == 'Тк' and tk.player == self.current_player:
                                torpedo_boat = tk
                    
                    # Remove both the torpedo and the selected target
                    for enemy in self.attackable_enemies:
                        if not enemy.hidden:  # Find the revealed target
                            # Сохраняем ссылки на корабли перед удалением
                            target = enemy
                            torpedo = self.selected_ship
                            # Удаляем сначала цель, потом торпеду
                            self.remove_ship(target)
                            self.remove_ship(torpedo)
                            
                            # If there's a torpedo boat, give it an additional move
                            if torpedo_boat:
                                self.selected_ship = torpedo_boat
                                self.highlighted_cells = self.get_possible_moves(torpedo_boat)
                                self.attackable_enemies = self.get_adjacent_enemies(torpedo_boat.position[0], torpedo_boat.position[1])
                                self.waiting_for_spacebar = False
                                # Don't change current player - ТК gets additional move
                                self.update_ship_visibility()
                                return
                            break
                    
                    # If no torpedo boat found, proceed normally
                    self.waiting_for_spacebar = False
                    self.selected_ship = None
                    self.highlighted_cells = []
                    self.attackable_enemies = []
                    self.current_player = 3 - self.current_player
                    self.update_ship_visibility()
                    return
                else:
                    # Regular combat result processing
                    self.process_combat_result()
                
                self.waiting_for_spacebar = False
                # Завершаем ход после боя – сбрасываем выбор и варианты хода/атаки
                self.selected_ship = None
                self.highlighted_cells = []
                self.attackable_enemies = []
                self.current_player = 3 - self.current_player
                self.tr_additional_move = False  # Reset the Тр additional move flag
                self.update_ship_visibility()
            return  # Пока ждём пробела, не обрабатываем прочие события

        if event.type == pygame.MOUSEBUTTONDOWN:
            current_time = pygame.time.get_ticks()
            cell = self.get_cell_from_mouse(event.pos)
            if cell:
                x, y = cell
                if cell == self.last_cell_clicked and current_time - self.last_click_time < 500:
                    # Обнаружено двойное нажатие
                    if self.selected_ship is not None:
                        if self.selected_ship.position == cell:
                            ship = self.selected_ship
                            self.selected_ship = None
                            self.highlighted_cells = []
                            self.attackable_enemies = []
                            if ship in self.previous_positions:
                                del self.previous_positions[ship]
                            self.current_player = 3 - self.current_player
                            self.update_ship_visibility()
                            self.last_cell_clicked = None
                            self.last_click_time = 0
                            return
                    else:
                        # Двойное нажатие без выбранного корабля
                        pass
                else:
                    self.last_cell_clicked = cell
                    self.last_click_time = current_time

                # Если корабль не выбран, выбираем его, если это наш корабль
                if self.selected_ship is None:
                    ship = self.board[x][y]
                    if ship and ship.player == self.current_player:
                        self.selected_ship = ship
                        self.highlighted_cells = self.get_possible_moves(ship)
                        adjacent_enemies = self.get_adjacent_enemies(x, y)
                        if adjacent_enemies:
                            self.attackable_enemies = adjacent_enemies
                else:
                    # Если нажали на ячейку, куда можно переместиться
                    if (x, y) in self.highlighted_cells:
                        from_x, from_y = self.selected_ship.position
                        moved = self.move_ship(self.selected_ship, (x, y))
                        if moved:
                            # После перемещения проверяем наличие врагов вокруг
                            adjacent_enemies = self.get_adjacent_enemies(x, y)
                            if adjacent_enemies:
                                self.attackable_enemies = adjacent_enemies
                            else:
                                # Если врагов рядом нет – завершаем ход
                                ship = self.selected_ship
                                self.selected_ship = None
                                self.highlighted_cells = []
                                self.attackable_enemies = []
                                if ship in self.previous_positions:
                                    del self.previous_positions[ship]
                                self.current_player = 3 - self.current_player
                                self.update_ship_visibility()
                        else:
                            # Некорректный ход – можно добавить сообщение
                            pass
                    else:
                        # Иначе проверяем, выбран ли враг для атаки
                        enemy = self.board[x][y]
                        if enemy and enemy.player != self.current_player and enemy in self.attackable_enemies:
                            # Special case for airplane attack
                            if self.selected_ship.type == 'С':
                                # Reveal all ships in the attack line
                                x, y = self.selected_ship.position
                                if self.current_player == 1:  # Player 1 moves up
                                    for dy in range(1, 6):  # Атакуем вниз
                                        ny = y + dy
                                        if 0 <= ny < GRID_HEIGHT:
                                            target = self.board[x][ny]
                                            if target and target.player != self.current_player:
                                                target.hidden = False  # Раскрываем фишку
                                else:  # Player 2 moves down
                                    for dy in range(-1, -6, -1):  # Атакуем вверх
                                        ny = y + dy
                                        if 0 <= ny < GRID_HEIGHT:
                                            target = self.board[x][ny]
                                            if target and target.player != self.current_player:
                                                target.hidden = False  # Раскрываем фишку
                                # Wait for spacebar to destroy the ships
                                self.waiting_for_spacebar = True
                                return
                            # Special case for torpedo attack
                            elif self.selected_ship.type == 'Т':
                                # Just show the selected target and wait for spacebar
                                enemy.hidden = False
                                self.waiting_for_spacebar = True
                                return
                            else:
                                # Regular combat initialization
                                self.battle_active = True
                                self.battle_attacker = self.current_player
                                self.battle_defender = 3 - self.current_player
                                self.battle_turn_player = self.current_player
                                self.attacking_ships = [self.selected_ship]
                                self.defending_ships = [enemy]
                                enemy.hidden = False  # Делаем видимой атакуемую фишку
                                self.attacking_passed = False
                                self.defending_passed = False
                                self.player_has_added_ships = False
                                self.waiting_for_spacebar = False
                                self.update_ship_visibility()
                                return
                        else:
                            # Некорректный выбор – можно сбрасывать выделение
                            pass
            else:
                # Если клик вне поля — отменяем выбор
                self.selected_ship = None
                self.highlighted_cells = []
                self.attackable_enemies = []
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.selected_ship and self.selected_ship in self.previous_positions:
                    # If this is an additional move for Тр after destroying a mine,
                    # and the ship has moved, end the turn
                    if self.tr_additional_move and self.selected_ship.type == 'Тр':
                        self.selected_ship = None
                        self.highlighted_cells = []
                        self.attackable_enemies = []
                        self.previous_positions = {}
                        self.tr_additional_move = False
                        self.current_player = 3 - self.current_player
                        self.update_ship_visibility()
                    else:
                        # Normal Esc behavior - return to original position
                        current_x, current_y = self.selected_ship.position
                        original_x, original_y = self.previous_positions[self.selected_ship]
                        self.board[current_x][current_y] = None
                        self.board[original_x][original_y] = self.selected_ship
                        self.selected_ship.position = (original_x, original_y)
                        del self.previous_positions[self.selected_ship]
                        self.selected_ship = None
                        self.highlighted_cells = []
                        self.attackable_enemies = []
                else:
                    self.selected_ship = None
                    self.highlighted_cells = []
                    self.attackable_enemies = []

    def handle_battle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            cell = self.get_cell_from_mouse(event.pos)
            if cell:
                x, y = cell
                ship = self.board[x][y]
                if ship and ship.player == self.battle_turn_player:
                    if self.battle_turn_player == self.battle_attacker:
                        if ship not in self.attacking_ships and len(self.attacking_ships) < 3:
                            if self.can_combine(self.attacking_ships, ship):
                                ship.hidden = False
                                self.attacking_ships.append(ship)
                                self.player_has_added_ships = True  # Игрок добавил фишку
                                # Сбрасываем флаг пасса соперника
                                self.defending_passed = False
                                self.update_ship_visibility()
                    else:
                        if ship not in self.defending_ships and len(self.defending_ships) < 3:
                            if self.can_combine(self.defending_ships, ship):
                                ship.hidden = False
                                self.defending_ships.append(ship)
                                self.player_has_added_ships = True  # Игрок добавил фишку
                                # Сбрасываем флаг пасса соперника
                                self.attacking_passed = False
                                self.update_ship_visibility()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self.player_has_added_ships == False:
                # Игрок пропустил ход
                if self.battle_turn_player == self.battle_attacker:
                    self.attacking_passed = True
                else:
                    self.defending_passed = True
            else:
                # Игрок не пропустил ход, но завершает свой раунд
                if self.battle_turn_player == self.battle_attacker:
                    self.attacking_passed = False
                else:
                    self.defending_passed = False
            # Проверяем, оба ли игрока подряд пропустили ход
            if self.attacking_passed and self.defending_passed:
                # Оба игрока пропустили подряд, завершаем бой
                self.process_combat_result()
                self.battle_active = False
                self.update_ship_visibility()
            else:
                # Передаем ход другому игроку
                self.battle_turn_player = self.battle_defender if self.battle_turn_player == self.battle_attacker else self.battle_attacker
                self.player_has_added_ships = False  # Сбрасываем флаг для нового игрока
                self.update_ship_visibility()

    def is_valid_position(self, pos):
        x, y = pos
        return 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT

    def move_ship(self, ship, new_position):
        if not self.is_valid_position(new_position):
            return False

        # Check if the position is occupied by another ship
        if self.board[new_position[0]][new_position[1]] is not None:
            return False

        # For regular mines, check if they can move
        if ship.type == 'ОМ':
            # Check if there's an Эс nearby (within 1 cell in any direction)
            has_es_nearby = False
            current_x, current_y = ship.position
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    check_x = current_x + dx
                    check_y = current_y + dy
                    if 0 <= check_x < GRID_WIDTH and 0 <= check_y < GRID_HEIGHT:
                        other_ship = self.board[check_x][check_y]
                        if other_ship and other_ship.type == 'Эс' and other_ship.player == ship.player:
                            has_es_nearby = True
                            break
                if has_es_nearby:
                    break
            
            if not has_es_nearby:
                return False

            # Check if the new position is adjacent to the same Эс
            has_es_at_new_pos = False
            new_x, new_y = new_position
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    check_x = new_x + dx
                    check_y = new_y + dy
                    if 0 <= check_x < GRID_WIDTH and 0 <= check_y < GRID_HEIGHT:
                        other_ship = self.board[check_x][check_y]
                        if other_ship and other_ship.type == 'Эс' and other_ship.player == ship.player:
                            has_es_at_new_pos = True
                            break
                if has_es_at_new_pos:
                    break
            
            if not has_es_at_new_pos:
                return False

        # For airplanes, check if they can move
        elif ship.type == 'С':
            # Check if there's an А nearby (within 1 cell in any direction)
            has_a_nearby = False
            current_x, current_y = ship.position
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    check_x = current_x + dx
                    check_y = current_y + dy
                    if 0 <= check_x < GRID_WIDTH and 0 <= check_y < GRID_HEIGHT:
                        other_ship = self.board[check_x][check_y]
                        if other_ship and other_ship.type == 'А' and other_ship.player == ship.player:
                            has_a_nearby = True
                            break
                if has_a_nearby:
                    break
            
            if not has_a_nearby:
                return False

            # Check if the new position is adjacent to the same А
            has_a_at_new_pos = False
            new_x, new_y = new_position
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    check_x = new_x + dx
                    check_y = new_y + dy
                    if 0 <= check_x < GRID_WIDTH and 0 <= check_y < GRID_HEIGHT:
                        other_ship = self.board[check_x][check_y]
                        if other_ship and other_ship.type == 'А' and other_ship.player == ship.player:
                            has_a_at_new_pos = True
                            break
                if has_a_at_new_pos:
                    break
            
            if not has_a_at_new_pos:
                return False

        # For torpedoes, check if they can move
        elif ship.type == 'Т':
            # Check if there's a Тк nearby (within 1 cell in any direction)
            has_tk_nearby = False
            current_x, current_y = ship.position
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    check_x = current_x + dx
                    check_y = current_y + dy
                    if 0 <= check_x < GRID_WIDTH and 0 <= check_y < GRID_HEIGHT:
                        other_ship = self.board[check_x][check_y]
                        if other_ship and other_ship.type == 'Тк' and other_ship.player == ship.player:
                            has_tk_nearby = True
                            break
                if has_tk_nearby:
                    break
            
            if not has_tk_nearby:
                return False

            # Check if the new position is adjacent to the same Тк
            has_tk_at_new_pos = False
            new_x, new_y = new_position
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue
                    check_x = new_x + dx
                    check_y = new_y + dy
                    if 0 <= check_x < GRID_WIDTH and 0 <= check_y < GRID_HEIGHT:
                        other_ship = self.board[check_x][check_y]
                        if other_ship and other_ship.type == 'Тк' and other_ship.player == ship.player:
                            has_tk_at_new_pos = True
                            break
                if has_tk_at_new_pos:
                    break
            
            if not has_tk_at_new_pos:
                return False

            # Check if the path is clear
            if not self.is_path_clear(current_x, current_y, new_x, new_y):
                return False

        # For other ships, check movement range
        elif ship.type != 'ОМ' and ship.type != 'С' and ship.type != 'Т':
            dx = abs(new_position[0] - ship.position[0])
            dy = abs(new_position[1] - ship.position[1])
            if dx + dy > ship.movement_range:
                return False

        # Update ship position
        old_x, old_y = ship.position
        new_x, new_y = new_position
        self.board[old_x][old_y] = None
        self.board[new_x][new_y] = ship
        ship.position = new_position
        return True

    def get_possible_moves(self, ship):
        moves = []
        x, y = ship.position
        for dx in range(-ship.movement_range, ship.movement_range + 1):
            for dy in range(-ship.movement_range, ship.movement_range + 1):
                if abs(dx) + abs(dy) <= ship.movement_range and (dx == 0 or dy == 0):
                    nx = x + dx
                    ny = y + dy
                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                        if self.board[nx][ny] is None:
                            if self.is_path_clear(x, y, nx, ny):
                                moves.append((nx, ny))
        return moves

    def is_path_clear(self, from_x, from_y, to_x, to_y):
        dx = to_x - from_x
        dy = to_y - from_y
        step_x = 0 if dx == 0 else dx // abs(dx)
        step_y = 0 if dy == 0 else dy // abs(dy)
        x, y = from_x, from_y
        while (x, y) != (to_x, to_y):
            x += step_x
            y += step_y
            if self.board[x][y] is not None:
                return False
        return True

    def get_adjacent_enemies(self, x, y):
        enemies = []
        ship = self.board[x][y]
        
        # Prevent mines from attacking on their own
        if ship and ship.type == 'М':
            return []
        
        # Special case for airplane in front of aircraft carrier
        if ship and ship.type == 'С':
            # Check if there's an aircraft carrier behind
            carrier_behind = False
            if self.current_player == 1:  # Player 1 moves up
                if y - 1 >= 0:  # Авианосец должен быть над самолетом
                    carrier = self.board[x][y - 1]
                    if carrier and carrier.type == 'А' and carrier.player == ship.player:
                        carrier_behind = True
            else:  # Player 2 moves down
                if y + 1 < GRID_HEIGHT:  # Авианосец должен быть под самолетом
                    carrier = self.board[x][y + 1]
                    if carrier and carrier.type == 'А' and carrier.player == ship.player:
                        carrier_behind = True

            if carrier_behind:
                # If airplane is in front of carrier, it can attack in a line
                if self.current_player == 1:  # Player 1 moves up
                    for dy in range(1, 6):  # Атакуем вниз
                        ny = y + dy
                        if 0 <= ny < GRID_HEIGHT:
                            # Add all cells in front of airplane as potential targets
                            target = self.board[x][ny]
                            if target and target.player != self.current_player:
                                enemies.append(target)
                            # Add empty cells as potential targets too
                            elif not target:
                                dummy_target = Ship("Dummy", 3 - self.current_player, "DUMMY")
                                dummy_target.position = (x, ny)
                                enemies.append(dummy_target)
                else:  # Player 2 moves down
                    for dy in range(-1, -6, -1):  # Атакуем вверх
                        ny = y + dy
                        if 0 <= ny < GRID_HEIGHT:
                            # Add all cells in front of airplane as potential targets
                            target = self.board[x][ny]
                            if target and target.player != self.current_player:
                                enemies.append(target)
                            # Add empty cells as potential targets too
                            elif not target:
                                dummy_target = Ship("Dummy", 3 - self.current_player, "DUMMY")
                                dummy_target.position = (x, ny)
                                enemies.append(dummy_target)
                return enemies

        # Special case for torpedo in front of torpedo boat
        elif ship and ship.type == 'Т':
            # Check if there's a torpedo boat behind
            tk_behind = False
            if self.current_player == 1:  # Player 1 moves up
                if y - 1 >= 0:  # Торпедный катер должен быть над торпедой
                    tk = self.board[x][y - 1]
                    if tk and tk.type == 'Тк' and tk.player == ship.player:
                        tk_behind = True
            else:  # Player 2 moves down
                if y + 1 < GRID_HEIGHT:  # Торпедный катер должен быть под торпедой
                    tk = self.board[x][y + 1]
                    if tk and tk.type == 'Тк' and tk.player == ship.player:
                        tk_behind = True

            if tk_behind:
                # If torpedo is in front of torpedo boat, it can attack in a specific pattern
                if self.current_player == 1:  # Player 1 moves up, torpedo attacks down
                    # Torpedo attack pattern for player 1:
                    # Row 1 (y+1): x-1,y+1  x,y+1  x+1,y+1
                    # Row 2 (y+2): x-1,y+2  x,y+2  x+1,y+2  
                    # Row 3 (y+3): x,y+3
                    
                    attack_positions = [
                        # Row 1
                        (x-1, y+1), (x, y+1), (x+1, y+1),
                        # Row 2
                        (x-1, y+2), (x, y+2), (x+1, y+2),
                        # Row 3
                        (x, y+3)
                    ]
                    
                    # Check each position, but stop at first obstacle in each column
                    blocked_columns = set()
                    
                    for pos_x, pos_y in attack_positions:
                        if 0 <= pos_x < GRID_WIDTH and 0 <= pos_y < GRID_HEIGHT:
                            # If this column is already blocked, skip
                            if pos_x in blocked_columns:
                                continue
                                
                            target = self.board[pos_x][pos_y]
                            if target:
                                if target.player != self.current_player:
                                    enemies.append(target)
                                # Block this column for further attacks
                                blocked_columns.add(pos_x)
                                
                else:  # Player 2 moves down, torpedo attacks up
                    # Torpedo attack pattern for player 2:
                    # Row 1 (y-1): x-1,y-1  x,y-1  x+1,y-1
                    # Row 2 (y-2): x-1,y-2  x,y-2  x+1,y-2
                    # Row 3 (y-3): x,y-3
                    
                    attack_positions = [
                        # Row 1
                        (x-1, y-1), (x, y-1), (x+1, y-1),
                        # Row 2
                        (x-1, y-2), (x, y-2), (x+1, y-2),
                        # Row 3
                        (x, y-3)
                    ]
                    
                    # Check each position, but stop at first obstacle in each column
                    blocked_columns = set()
                    
                    for pos_x, pos_y in attack_positions:
                        if 0 <= pos_x < GRID_WIDTH and 0 <= pos_y < GRID_HEIGHT:
                            # If this column is already blocked, skip
                            if pos_x in blocked_columns:
                                continue
                                
                            target = self.board[pos_x][pos_y]
                            if target:
                                if target.player != self.current_player:
                                    enemies.append(target)
                                # Block this column for further attacks
                                blocked_columns.add(pos_x)
                                
                return enemies

        # Regular case for other ships
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                enemy = self.board[x][ny]
                if enemy and enemy.player != self.current_player:
                    if self.is_enemy_in_front((x, y), (nx, ny)):
                        enemies.append(enemy)
        return enemies

    def is_enemy_in_front(self, from_pos, enemy_pos):
        x1, y1 = from_pos
        x2, y2 = enemy_pos
        if self.current_player == 2:
            # Для Игрока 2, корабль противника считается «впереди», если он сверху
            return x1 == x2 and y2 == y1 - 1
        elif self.current_player == 1:
            # Для Игрока 1 противник считается вперёд, если он снизу
            return x1 == x2 and y2 == y1 + 1
        else:
            return False

    def resolve_combat(self, attacking_ships, defending_ships):
        pass  # Этот метод больше не используется

    def process_combat_result(self):
        attacking_group = self.attacking_ships.copy()  # ИСПРАВЛЕНО: создаем копию списка
        defending_group = self.defending_ships.copy()  # ИСПРАВЛЕНО: создаем копию списка
        print("=== Combat Debug ===")
        print("Total attacking_ships in self.attacking_ships:", len(self.attacking_ships))
        print("Total defending_ships in self.defending_ships:", len(self.defending_ships))
        print("Attacking ships (copy):", [f"{ship.name}({ship.position})" for ship in attacking_group])
        print("Defending ships (copy):", [f"{ship.name}({ship.position})" for ship in defending_group])
        print("About to process combat with", len(attacking_group), "attackers vs", len(defending_group), "defenders")

        # Проверяем наличие Танкера в атакующей группе
        tankers = [ship for ship in attacking_group if ship.type == 'Тн']
        if tankers:
            print("Tanker detected in attack group")
            # Сохраняем текущего игрока как атакующего для правильной передачи хода
            self.battle_attacker = self.current_player
            # Уничтожаем первую цель и танкер с пропуском автоматической очистки
            if defending_group:
                self.remove_ship(defending_group[0], skip_cleanup=True)
            self.remove_ship(tankers[0], skip_cleanup=True)
            # Вызываем очистку один раз в конце
            self.cleanup_after_combat()
            return

        # Проверяем наличие Танкера в защищающейся группе
        tankers = [ship for ship in defending_group if ship.type == 'Тн']
        if tankers:
            print("Tanker detected in defense group")
            # Сохраняем текущего игрока как атакующего для правильной передачи хода
            self.battle_attacker = self.current_player
            # Уничтожаем первого атакующего и танкер с пропуском автоматической очистки
            if attacking_group:
                self.remove_ship(attacking_group[0], skip_cleanup=True)
            self.remove_ship(tankers[0], skip_cleanup=True)
            # Вызываем очистку один раз в конце
            self.cleanup_after_combat()
            return

        # Check for atomic bombs first
        atomic_bombs = [ship for ship in attacking_group if ship.type == 'АБ']
        if atomic_bombs:
            print("Atomic bomb detected")
            # Set battle_attacker to ensure turn is passed to the opponent after cleanup
            self.battle_attacker = self.current_player
            
            affected_positions = []
            for bomb in atomic_bombs:
                x, y = bomb.position
                # Get all positions in a 5x5 square centered on the bomb
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                            affected_positions.append((nx, ny))
            
            # Destroy all ships in affected positions with skip_cleanup
            for pos in affected_positions:
                x, y = pos
                ship = self.board[x][y]
                if ship:
                    self.remove_ship(ship, skip_cleanup=True)
            
            # Call cleanup once after all ships are removed
            self.cleanup_after_combat()
            return

        # Special case: КРПЛ always beats Кр regardless of attack/defense position
        krpl_in_attack = any(ship.type == 'КРПЛ' for ship in attacking_group)
        krpl_in_defense = any(ship.type == 'КРПЛ' for ship in defending_group)
        kr_in_attack = any(ship.type == 'Кр' for ship in attacking_group)
        kr_in_defense = any(ship.type == 'Кр' for ship in defending_group)
        
        print("Combat check КРПЛ vs Кр:")
        print(f"КРПЛ in attack: {krpl_in_attack}")
        print(f"КРПЛ in defense: {krpl_in_defense}")
        print(f"Кр in attack: {kr_in_attack}")
        print(f"Кр in defense: {kr_in_defense}")
        
        # If КРПЛ and Кр are fighting (in any configuration), КРПЛ always wins
        if (krpl_in_attack and kr_in_defense) or (krpl_in_defense and kr_in_attack):
            print("КРПЛ vs Кр special rule triggered!")
            # Сохраняем текущего игрока как атакующего для правильной передачи хода
            self.battle_attacker = self.current_player
            if krpl_in_attack:
                print("КРПЛ is attacking - destroying defenders")
                # КРПЛ is attacking, destroy all defenders with skip_cleanup
                for ship in defending_group:
                    self.remove_ship(ship, skip_cleanup=True)
            else:
                print("КРПЛ is defending - destroying attackers")
                # КРПЛ is defending, destroy attackers with skip_cleanup
                for ship in attacking_group:
                    self.remove_ship(ship, skip_cleanup=True)
            
            # Call cleanup once after all ships are removed
            self.cleanup_after_combat()
            return

        # Check for airplane special attack
        attacking_airplanes = [ship for ship in attacking_group if ship.type == 'С']
        if attacking_airplanes:
            for airplane in attacking_airplanes:
                x, y = airplane.position
                # Check if there's an aircraft carrier behind
                carrier_behind = False
                if self.current_player == 1:  # Player 1 moves up
                    if y - 1 >= 0:  # Авианосец должен быть над самолетом
                        carrier = self.board[x][y - 1]
                        if carrier and carrier.type == 'А' and carrier.player == airplane.player:
                            carrier_behind = True
                else:  # Player 2 moves down
                    if y + 1 < GRID_HEIGHT:  # Авианосец должен быть под самолетом
                        carrier = self.board[x][y + 1]
                        if carrier and carrier.type == 'А' and carrier.player == airplane.player:
                            carrier_behind = True

                if carrier_behind:
                    # Сохраняем текущего игрока как атакующего для правильной передачи хода
                    self.battle_attacker = self.current_player
                    # Remove all ships in the attack line including the airplane with skip_cleanup
                    if self.current_player == 1:  # Player 1 moves up
                        for dy in range(0, 6):  # Include the airplane's position (dy=0)
                            ny = y + dy
                            if 0 <= ny < GRID_HEIGHT:
                                target = self.board[x][ny]
                                if target:
                                    self.remove_ship(target, skip_cleanup=True)
                    else:  # Player 2 moves down
                        for dy in range(0, -6, -1):  # Include the airplane's position (dy=0)
                            ny = y + dy
                            if 0 <= ny < GRID_HEIGHT:
                                target = self.board[x][ny]
                                if target:
                                    self.remove_ship(target, skip_cleanup=True)
                    
                    # Call cleanup once after all ships are removed
                    self.cleanup_after_combat()
                    return

        # Check for torpedo special attack
        attacking_torpedoes = [ship for ship in attacking_group if ship.type == 'Т']
        if attacking_torpedoes:
            for torpedo in attacking_torpedoes:
                x, y = torpedo.position
                # Check if there's a torpedo boat behind
                tk_behind = None
                if self.current_player == 1:  # Player 1 moves up
                    if y - 1 >= 0:  # Торпедный катер должен быть над торпедой
                        tk = self.board[x][y - 1]
                        if tk and tk.type == 'Тк' and tk.player == torpedo.player:
                            tk_behind = tk
                else:  # Player 2 moves down
                    if y + 1 < GRID_HEIGHT:  # Торпедный катер должен быть под торпедой
                        tk = self.board[x][y + 1]
                        if tk and tk.type == 'Тк' and tk.player == torpedo.player:
                            tk_behind = tk

                if tk_behind:
                    # Store the attacker player number before clearing battle state
                    attacker_player = self.battle_attacker
                    
                    # Find and destroy the selected target with skip_cleanup
                    for enemy in self.attackable_enemies:
                        if enemy in defending_group:
                            # Destroy both the target and the torpedo with skip_cleanup
                            self.remove_ship(enemy, skip_cleanup=True)
                            self.remove_ship(torpedo, skip_cleanup=True)
                            break
                    
                    # Reset battle state
                    self.battle_active = False
                    self.waiting_for_spacebar = False
                    self.attacking_ships = []
                    self.defending_ships = []
                    self.battle_turn_player = None
                    self.battle_attacker = None
                    self.battle_defender = None
                    
                    # Give the torpedo boat an additional move
                    self.selected_ship = tk_behind
                    self.highlighted_cells = self.get_possible_moves(tk_behind)
                    self.attackable_enemies = self.get_adjacent_enemies(tk_behind.position[0], tk_behind.position[1])
                    
                    # Make sure the current player is the attacker (not None)
                    self.current_player = attacker_player
                    
                    # Update ship visibility to make the current player's ships visible
                    self.update_ship_visibility()
                    return
                    
                return

        # Special case: Тр attacking mines - only destroy the mine, not the Тр
        tr_ships = [ship for ship in attacking_group if ship.type == 'Тр']
        mines = [ship for ship in defending_group if ship.type == 'М']
        if tr_ships and mines:
            # Store the attacker player number before clearing battle state
            attacker_player = self.battle_attacker
            
            # Only destroy the mines with skip_cleanup
            for mine in mines:
                self.remove_ship(mine, skip_cleanup=True)
                
            # Reset battle state
            self.battle_active = False
            self.waiting_for_spacebar = False
            self.attacking_ships = []
            self.defending_ships = []
            self.battle_turn_player = None
            self.battle_attacker = None
            self.battle_defender = None
            
            # Don't destroy the Тр ships - they get an additional action
            self.selected_ship = tr_ships[0]  # Keep the Тр ship selected for another action
            self.highlighted_cells = self.get_possible_moves(tr_ships[0])
            self.attackable_enemies = self.get_adjacent_enemies(tr_ships[0].position[0], tr_ships[0].position[1])
            
            # Make sure the current player is the attacker (not None)
            self.current_player = attacker_player
            
            # Set flag to indicate this is an additional move after destroying a mine
            self.tr_additional_move = True
            
            # Update ship visibility to make the current player's ships visible
            self.update_ship_visibility()
            return

        # Check for regular mines
        regular_mines = [ship for ship in defending_group if ship.type == 'ОМ']
        if regular_mines:
            # Сохраняем текущего игрока как атакующего для правильной передачи хода
            self.battle_attacker = self.current_player
            # Destroy the first attacking ship and the mine with skip_cleanup
            if attacking_group:
                self.remove_ship(attacking_group[0], skip_cleanup=True)
            for mine in regular_mines:
                self.remove_ship(mine, skip_cleanup=True)
            
            # Call cleanup once after all ships are removed
            self.cleanup_after_combat()
            return

        # Check for stationary mines
        mines = [ship for ship in defending_group if ship.type == 'М']
        if mines:
            # Сохраняем текущего игрока как атакующего для правильной передачи хода
            self.battle_attacker = self.current_player
            # Destroy all attacking ships and mines with skip_cleanup
            for ship in attacking_group + mines:
                self.remove_ship(ship, skip_cleanup=True)
            
            # Call cleanup once after all ships are removed
            self.cleanup_after_combat()
            return

        # Check if attacker has Пл and defender has А
        pl_attacking = any(ship.type == 'Пл' for ship in attacking_group)
        a_defending = any(ship.type == 'А' for ship in defending_group)
        if pl_attacking and a_defending:
            # Сохраняем текущего игрока как атакующего для правильной передачи хода
            self.battle_attacker = self.current_player
            # Пл always beats А, regardless of total ratings
            for ship in defending_group:
                self.remove_ship(ship, skip_cleanup=True)
            
            # Call cleanup once after all ships are removed
            self.cleanup_after_combat()
            return
            
        # Check if attacker has Пл and defender has БДК
        pl_attacking = any(ship.type == 'Пл' for ship in attacking_group)
        bdk_defending = any(ship.type == 'БДК' for ship in defending_group)
        if pl_attacking and bdk_defending:
            # Сохраняем текущего игрока как атакующего для правильной передачи хода
            self.battle_attacker = self.current_player
            # Пл always beats БДК, regardless of total ratings
            for ship in defending_group:
                self.remove_ship(ship, skip_cleanup=True)
            
            # Call cleanup once after all ships are removed
            self.cleanup_after_combat()
            return

        # Check for airplane combat rules (when airplane is not doing special attack)
        # Airplane in attack position always wins, airplane not in attack position always loses
        attacking_airplanes = [ship for ship in attacking_group if ship.type == 'С']
        defending_airplanes = [ship for ship in defending_group if ship.type == 'С']
        
        # Check attacking airplanes
        for airplane in attacking_airplanes:
            x, y = airplane.position
            carrier_behind = False
            if self.current_player == 1:  # Player 1 moves up
                if y - 1 >= 0:  # Авианосец должен быть над самолетом
                    carrier = self.board[x][y - 1]
                    if carrier and carrier.type == 'А' and carrier.player == airplane.player:
                        carrier_behind = True
            else:  # Player 2 moves down
                if y + 1 < GRID_HEIGHT:  # Авианосец должен быть под самолетом
                    carrier = self.board[x][y + 1]
                    if carrier and carrier.type == 'А' and carrier.player == airplane.player:
                        carrier_behind = True
            
            if carrier_behind:
                # Airplane in attack position always wins - destroy all defenders
                self.battle_attacker = self.current_player
                for ship in defending_group:
                    self.remove_ship(ship, skip_cleanup=True)
                self.cleanup_after_combat()
                return
            else:
                # Airplane not in attack position always loses - destroy the airplane
                self.battle_attacker = self.current_player
                self.remove_ship(airplane, skip_cleanup=True)
                self.cleanup_after_combat()
                return
        
        # Check defending airplanes
        for airplane in defending_airplanes:
            x, y = airplane.position
            carrier_behind = False
            # For defending airplane, we need to check the opposite direction
            # Since defending airplane faces the attacker
            if self.current_player == 1:  # Player 1 is attacking, so defender faces up
                if y + 1 < GRID_HEIGHT:  # Авианосец должен быть под самолетом для обороны
                    carrier = self.board[x][y + 1]
                    if carrier and carrier.type == 'А' and carrier.player == airplane.player:
                        carrier_behind = True
            else:  # Player 2 is attacking, so defender faces down
                if y - 1 >= 0:  # Авианосец должен быть над самолетом для обороны
                    carrier = self.board[x][y - 1]
                    if carrier and carrier.type == 'А' and carrier.player == airplane.player:
                        carrier_behind = True
            
            if carrier_behind:
                # Defending airplane in attack position always wins - destroy all attackers
                self.battle_attacker = self.current_player
                for ship in attacking_group:
                    self.remove_ship(ship, skip_cleanup=True)
                self.cleanup_after_combat()
                return
            else:
                # Defending airplane not in attack position always loses - destroy the airplane
                self.battle_attacker = self.current_player
                self.remove_ship(airplane, skip_cleanup=True)
                self.cleanup_after_combat()
                return

        # Regular combat resolution
        # Сохраняем текущего игрока как атакующего для правильной передачи хода
        self.battle_attacker = self.current_player
        attacking_rating = sum(ship.rating for ship in attacking_group)
        defending_rating = sum(ship.rating for ship in defending_group)

        print(f"Combat ratings: Attacking {attacking_rating} vs Defending {defending_rating}")

        if attacking_rating > defending_rating:
            # Attacking ships win - remove defending ships with skip_cleanup
            print("Attackers win! Removing", len(defending_group), "defending ships")
            for ship in defending_group:  # ИСПРАВЛЕНО: используем копию списка
                self.remove_ship(ship, skip_cleanup=True)
        elif defending_rating > attacking_rating:
            # Defending ships win - remove attacking ships with skip_cleanup
            print("Defenders win! Removing", len(attacking_group), "attacking ships")
            for ship in attacking_group:  # ИСПРАВЛЕНО: используем копию списка
                self.remove_ship(ship, skip_cleanup=True)
        else:
            # Both sides destroy each other - remove all ships with skip_cleanup
            print("Draw! Removing all", len(attacking_group + defending_group), "ships")
            for ship in attacking_group + defending_group:  # ИСПРАВЛЕНО: используем копии списков
                self.remove_ship(ship, skip_cleanup=True)
                
        # Call cleanup once after all ships are removed
        self.cleanup_after_combat()

    def cleanup_after_combat(self):
        # Передаем ход следующему игроку перед сбросом переменных боя
        if self.battle_attacker is not None:
            self.current_player = 3 - self.battle_attacker
        else:
            self.current_player = 3 - self.current_player

        # Сбрасываем выбор и подсветку после боя
        self.selected_ship = None
        self.highlighted_cells = []
        self.attackable_enemies = []

        # Сбрасываем боевые состояния
        self.attacking_ships = []
        self.defending_ships = []
        self.attacking_passed = False
        self.defending_passed = False
        self.player_has_added_ships = False
        self.battle_turn_player = None
        self.battle_attacker = None
        self.battle_defender = None
        self.battle_active = False
        self.waiting_for_spacebar = False
        # Обновляем видимость фишек после боя
        self.update_ship_visibility()

        # Check ВМБ count win condition
        base_count_player1 = sum(1 for ship in self.player1_ships if ship.type == 'ВМБ')
        base_count_player2 = sum(1 for ship in self.player2_ships if ship.type == 'ВМБ')

        if base_count_player1 == 0 and len(self.player1_ships) > 0:
            self.game_over(winner=2)
        elif base_count_player2 == 0 and len(self.player2_ships) > 0:
            self.game_over(winner=1)
        elif len(self.player1_ships) == 0:
            self.game_over(winner=2)
        elif len(self.player2_ships) == 0:
            self.game_over(winner=1)
        # (Больше не завершаем игру автоматически при отсутствии ходов)

    def can_player_make_move(self, player):
        """Check if a player has any ships that can move independently."""
        ships = self.player1_ships if player == 1 else self.player2_ships
        
        # Check if player has any ships that can move on their own
        for ship in ships:
            # Skip mines, they can't move on their own
            if ship.type == 'М':
                continue
                
            # Skip fixed bases
            if ship.type == 'ВМБ':
                continue
                
            # For airplane, check if it has an aircraft carrier adjacent
            if ship.type == 'С':
                x, y = ship.position
                has_carrier = False
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                        adj_ship = self.board[nx][ny]
                        if adj_ship and adj_ship.type == 'А' and adj_ship.player == player:
                            has_carrier = True
                            break
                if not has_carrier:
                    continue
                    
            # For torpedo, check if it has a torpedo boat adjacent
            if ship.type == 'Т':
                x, y = ship.position
                has_torpedo_boat = False
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                        adj_ship = self.board[nx][ny]
                        if adj_ship and adj_ship.type == 'Тк' and adj_ship.player == player:
                            has_torpedo_boat = True
                            break
                if not has_torpedo_boat:
                    continue
                    
            # If we got here, this ship can potentially move
            possible_moves = self.get_possible_moves(ship)
            if possible_moves:
                return True
                
        # If we checked all ships and found none that can move, return False
        return False

    def game_over(self, winner):
        if self.online_session:
            self.winner = winner
            self.sync_to_firebase()
        font = pygame.font.Font(None, 72)
        text = font.render(f"Player {winner} Wins!", True, RED)
        self.screen.blit(text, (WINDOW_SIZE // 2 - text.get_width() // 2, WINDOW_SIZE // 2))
        pygame.display.flip()
        pygame.time.wait(5000)
        pygame.quit()
        sys.exit()

    def get_combined_ships(self, ship):
        visited = set()
        queue = [ship]
        group = []
        while queue:
            current_ship = queue.pop(0)
            if current_ship in visited:
                continue
            visited.add(current_ship)
            group.append(current_ship)
            x, y = current_ship.position
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    neighbor = self.board[nx][ny]
                    if neighbor and neighbor.player == current_ship.player and neighbor.type in current_ship.combine_with:
                        queue.append(neighbor)
        return group

    def update_ship_visibility(self):
        for ship in self.player1_ships + self.player2_ships:
            if self.battle_active:
                if ship in self.attacking_ships + self.defending_ships:
                    ship.hidden = False  # Фишки, участвующие в бою, всегда видимы
                else:
                    ship.hidden = (ship.player != self.battle_turn_player)
            else:
                ship.hidden = (ship.player != self.current_player)

        # Устанавливаем видимость для возвращённых фишек
        if self.current_player == 1:
            for ship in self.captured_ships_player1:
                ship.hidden = False
            for ship in self.captured_ships_player2:
                ship.hidden = True
        else:
            for ship in self.captured_ships_player2:
                ship.hidden = False
            for ship in self.captured_ships_player1:
                ship.hidden = True

    def can_combine(self, group_ships, new_ship):
        for ship in group_ships:
            if self.are_ships_adjacent(ship, new_ship) and new_ship.type in ship.combine_with:
                return True
        return False

    def are_ships_adjacent(self, ship1, ship2):
        x1, y1 = ship1.position
        x2, y2 = ship2.position
        return abs(x1 - x2) + abs(y1 - y2) == 1

    def draw_board(self):
        self.screen.fill(WHITE)
        
        # Рисуем сетку
        # Горизонтальные линии
        for i in range(GRID_HEIGHT + 1):
            y = i
            if self.is_flipped():
                y = GRID_HEIGHT - i
            pygame.draw.line(self.screen, BLACK,
                             (self.margin_x, self.margin_y + y * self.cell_size),
                             (self.margin_x + GRID_WIDTH * self.cell_size, self.margin_y + y * self.cell_size))
        # Вертикальные линии
        for i in range(GRID_WIDTH + 1):
            pygame.draw.line(self.screen, BLACK,
                             (self.margin_x + i * self.cell_size, self.margin_y),
                             (self.margin_x + i * self.cell_size, self.margin_y + GRID_HEIGHT * self.cell_size))
        
        # Рисуем корабли на поле
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                ship = self.board[x][y]
                if ship:
                    draw_x, draw_y = self.transform_coords(x, y)
                    rect = pygame.Rect(self.margin_x + draw_x * self.cell_size + 2,
                                     self.margin_y + draw_y * self.cell_size + 2,
                                     self.cell_size - 4, self.cell_size - 4)
                    # Если корабль участвовал в бою (combat_info активен), то его рисуем с его собственным цветом,
                    # игнорируя текущего игрока.
                    if self.combat_info is not None and (ship in self.combat_info.get('attacking_group', []) or 
                                                      ship in self.combat_info.get('defending_group', [])):
                        ship.draw(self.screen, rect, current_player=ship.player)
                    else:
                        ship.draw(self.screen, rect, current_player=self.current_player)
        
        # Рисуем неразмещённые корабли (на этапе setup)
        menu_ship_size = int(MENU_SHIP_SIZE * self.scale_factor)
        if self.phase == 'setup':
            if self.current_player == 1:
                for ship in self.unplaced_ships_player1:
                    rect = pygame.Rect(ship.position[0],
                                     ship.position[1],
                                     menu_ship_size, menu_ship_size)
                    ship.draw(self.screen, rect, current_player=self.current_player)
            else:
                for ship in self.unplaced_ships_player2:
                    rect = pygame.Rect(ship.position[0],
                                     ship.position[1],
                                     menu_ship_size, menu_ship_size)
                    ship.draw(self.screen, rect, current_player=self.current_player)
        else:
            captured_ships = self.captured_ships_player1 if self.current_player == 1 else self.captured_ships_player2
            for idx, ship in enumerate(captured_ships):
                # Назначаем позиции для фишек на стороне доски
                x = self.margin_x + idx * (self.cell_size + 10)
                if self.current_player == 1:
                    y = self.margin_y // 2 - self.cell_size  # Сверху доски
                else:
                    y = self.screen.get_height() - self.margin_y // 2  # Снизу доски
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                ship.hidden = False  # Убеждаемся, что фишка видима
                ship.draw(self.screen, rect)

        # Подсветка возможных ходов (желтая, с прозрачностью)
        if self.highlighted_cells:
            for cell in self.highlighted_cells:
                draw_x, draw_y = self.transform_coords(cell[0], cell[1])
                rect = pygame.Rect(self.margin_x + draw_x * self.cell_size + 2,
                                 self.margin_y + draw_y * self.cell_size + 2,
                                 self.cell_size - 4, self.cell_size - 4)
                overlay = pygame.Surface((self.cell_size - 4, self.cell_size - 4), pygame.SRCALPHA)
                overlay.fill((YELLOW[0], YELLOW[1], YELLOW[2], 128))
                self.screen.blit(overlay, rect.topleft)

        # Подсветка возможных целей для атаки (зелёная, с прозрачностью)
        if self.attackable_enemies:
            for enemy in self.attackable_enemies:
                x, y = enemy.position
                draw_x, draw_y = self.transform_coords(x, y)
                rect = pygame.Rect(self.margin_x + draw_x * self.cell_size + 2,
                                 self.margin_y + draw_y * self.cell_size + 2,
                                 self.cell_size - 4, self.cell_size - 4)
                overlay = pygame.Surface((self.cell_size - 4, self.cell_size - 4), pygame.SRCALPHA)
                overlay.fill((GREEN[0], GREEN[1], GREEN[2], 128))
                self.screen.blit(overlay, rect.topleft)

        # Подсветка выбранного корабля
        if self.selected_ship and self.phase != 'setup':
            x, y = self.selected_ship.position
            draw_x, draw_y = self.transform_coords(x, y)
            color = LIGHT_BLUE if self.current_player == 1 else LIGHT_RED
            pygame.draw.rect(self.screen, color,
                           (self.margin_x + draw_x * self.cell_size, self.margin_y + draw_y * self.cell_size,
                            self.cell_size, self.cell_size), 3)
        
        # Вычисляем масштабированные размеры шрифтов
        font_size_large = int(28 * self.scale_factor)
        font_size_small = int(22 * self.scale_factor)
        
        # Отображаем сообщения в зависимости от состояния игры
        font = pygame.font.Font(None, font_size_large)
        if self.phase == 'setup':
            text = font.render(f"Игрок {self.current_player} расставляет корабли", True, BLACK)
            self.screen.blit(text, (10, 10))
            font = pygame.font.Font(None, font_size_small)
            text = font.render("Перетащите корабли на свою сторону доски", True, BLACK)
            self.screen.blit(text, (10, 40))
        elif self.battle_active:
            text = font.render("Фаза атаки!", True, BLACK)
            self.screen.blit(text, (10, 10))
            font = pygame.font.Font(None, font_size_small)
            if self.attacking_passed and self.defending_passed:
                text = font.render("Бой завершён, нажмите ПРОБЕЛ", True, BLACK)
                self.screen.blit(text, (10, 40))
            else:
                if self.battle_turn_player == self.battle_attacker:
                    instruction = "Игрок 1: выберите фишки для атаки"
                else:
                    instruction = "Игрок 2: выберите фишки для защиты"
                text = font.render(instruction, True, BLACK)
                self.screen.blit(text, (10, 40))
                text = font.render("Когда закончите выбор, нажмите ПРОБЕЛ", True, BLACK)
                self.screen.blit(text, (10, 65))
                
            for ship in self.attacking_ships:
                if ship.position is not None:
                    x, y = ship.position
                    pygame.draw.rect(self.screen, YELLOW,
                                    (self.margin_x + x * self.cell_size, self.margin_y + y * self.cell_size,
                                    self.cell_size, self.cell_size), 3)
            for ship in self.defending_ships:
                if ship.position is not None:
                    x, y = ship.position
                    pygame.draw.rect(self.screen, GREEN,
                                    (self.margin_x + x * self.cell_size, self.margin_y + y * self.cell_size,
                                    self.cell_size, self.cell_size), 3)
        else:
            text = font.render(f"Ход игрока {self.current_player}", True, BLACK)
            self.screen.blit(text, (10, 10))
            font = pygame.font.Font(None, font_size_small)
            if self.selected_ship is None:
                text = font.render("Выберите корабль для перемещения", True, BLACK)
                self.screen.blit(text, (10, 40))
            else:
                if self.attackable_enemies:
                    text = font.render("Выберите врага для атаки или переместитесь", True, BLACK)
                    self.screen.blit(text, (10, 40))
                else:
                    text = font.render("Выберите клетку для перемещения", True, BLACK)
                    self.screen.blit(text, (10, 40))
        if self.waiting_for_spacebar:
            font = pygame.font.Font(None, font_size_small)
            text = font.render("Нажмите ПРОБЕЛ для продолжения", True, BLACK)
            self.screen.blit(text, (10, 90))

        # Отображаем сообщение о необходимости нажать пробел
        if self.setup_message:
            font = pygame.font.Font(None, font_size_large)
            text = font.render(self.setup_message, True, BLACK)
            text_rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() - 50))
            self.screen.blit(text, text_rect)
        
        # Рисуем кнопку случайной расстановки в фазе setup
        if self.phase == 'setup':
            # Рисуем кнопку
            pygame.draw.rect(self.screen, LIGHT_BLUE, self.random_button_rect)
            pygame.draw.rect(self.screen, BLACK, self.random_button_rect, 2)  # Обводка
            
            # Текст кнопки
            font_size = int(18 * self.scale_factor)
            button_text = "Случайно"
            
            font = pygame.font.Font(None, font_size)
            text = font.render(button_text, True, BLACK)
            text_rect = text.get_rect(center=self.random_button_rect.center)
            self.screen.blit(text, text_rect)
        
        # === TIMER DISPLAY ===
        font = pygame.font.Font(None, 28)
        # Расстановка
        if self.phase == 'setup':
            t1 = str(datetime.timedelta(seconds=int(self.setup_time[1])))
            t2 = str(datetime.timedelta(seconds=int(self.setup_time[2])))
            text = font.render(f"Время на расстановку: Игрок 1: {t1} | Игрок 2: {t2}", True, (0,0,0))
            self.screen.blit(text, (10, self.screen.get_height()-30))
        # Игра
        else:
            t1 = str(datetime.timedelta(seconds=int(self.total_time[1])))
            t2 = str(datetime.timedelta(seconds=int(self.total_time[2])))
            text = font.render(f"Общее время: Игрок 1: {t1} | Игрок 2: {t2}", True, (0,0,0))
            self.screen.blit(text, (10, self.screen.get_height()-60))
            # Таймер хода
            move_t = str(datetime.timedelta(seconds=int(self.current_move_timer)))
            text2 = font.render(f"Время на ход: {move_t}", True, (0,0,0))
            self.screen.blit(text2, (10, self.screen.get_height()-30))
            # Кнопки паузы
            if not self.pause_active:
                y = self.screen.get_height()-100
                if self.pauses[self.current_player]["long"]:
                    pygame.draw.rect(self.screen, (200,200,100), (400, y, 140, 32))
                    self.screen.blit(font.render("Пауза 3 мин", True, (0,0,0)), (410, y+4))
                if self.pauses[self.current_player]["short"]:
                    pygame.draw.rect(self.screen, (180,220,180), (560, y, 120, 32))
                    self.screen.blit(font.render("Пауза 1 мин", True, (0,0,0)), (570, y+4))
            else:
                y = self.screen.get_height()-100
                text = font.render(f"Пауза: {self.pause_type} ({self.pause_owner})", True, (0,0,0))
                self.screen.blit(text, (400, y-30))
        
        # === Табличка убитых фишек соперника ===
        font = pygame.font.Font(None, 24)
        # Определяем, кого показывать
        if self.is_flipped():
            # Я игрок 2, показываем убитые фишки игрока 1
            captured = self.captured_ships_player2
            enemy_ships = self.player1_ships + self.captured_ships_player2
        else:
            # Я игрок 1, показываем убитые фишки игрока 2
            captured = self.captured_ships_player1
            enemy_ships = self.player2_ships + self.captured_ships_player1
        # Считаем всего по типам у соперника
        type_total = {}
        for ship in enemy_ships:
            if ship.type not in type_total:
                type_total[ship.type] = 0
            type_total[ship.type] += 1
        # Считаем убитых по типам
        type_killed = {}
        for ship in captured:
            if ship.type not in type_killed:
                type_killed[ship.type] = 0
            type_killed[ship.type] += 1
        # Рисуем табличку
        x0 = self.screen.get_width() - 180
        y0 = 40
        self.screen.blit(font.render("Убитые фишки соперника:", True, (0,0,0)), (x0, y0))
        y = y0 + 30
        for stype in sorted(type_total.keys()):
            killed = type_killed.get(stype, 0)
            total = type_total[stype]
            text = f"{stype}: {killed}/{total}"
            self.screen.blit(font.render(text, True, (0,0,0)), (x0, y))
            y += 22
        
        pygame.display.flip()

    def remove_ship(self, ship, skip_cleanup=False):
        if ship is None:
            return
        print(f"[DEBUG] Удаляется корабль: {ship.name} (тип: {ship.type}, игрок: {ship.player}, позиция: {ship.position})")
        # Сохраняем позицию перед удалением
        position = ship.position if hasattr(ship, 'position') else None
        # Удаляем корабль из списков игроков
        if ship in self.player1_ships:
            self.player1_ships.remove(ship)
        if ship in self.player2_ships:
            self.player2_ships.remove(ship)
        # Очищаем позицию на доске, если она была
        if position:
            x, y = position
            self.board[x][y] = None
        # Очищаем состояние после боя только если не указано пропустить
        if not skip_cleanup:
            self.cleanup_after_combat()

    def place_ships_randomly(self):
        """Расставляет корабли текущего игрока случайным образом"""
        
        # Определяем диапазон строк для текущего игрока
        if self.current_player == 1:
            row_range = range(0, 5)  # Первые 5 строк для первого игрока
        else:
            row_range = range(GRID_HEIGHT - 5, GRID_HEIGHT)  # Последние 5 строк для второго игрока
            
        # Сначала удаляем все корабли с доски, которые принадлежат текущему игроку
        for x in range(GRID_WIDTH):
            for y in row_range:
                if self.board[x][y] and self.board[x][y].player == self.current_player:
                    ship = self.board[x][y]
                    self.board[x][y] = None
                    if self.current_player == 1:
                        if ship in self.player1_ships:
                            self.player1_ships.remove(ship)
                            self.unplaced_ships_player1.append(ship)
                    else:
                        if ship in self.player2_ships:
                            self.player2_ships.remove(ship)
                            self.unplaced_ships_player2.append(ship)
        
        # Получаем список неразмещенных кораблей
        unplaced_ships = self.unplaced_ships_player1 if self.current_player == 1 else self.unplaced_ships_player2
        
        # Создаем копию списка, чтобы не изменять его во время итерации
        ships_to_place = unplaced_ships.copy()
        
        # Сначала размещаем базы и важные фишки
        priority_types = ["ВМБ", "СМ", "КРПЛ", "Пл", "АБ", "А"]
        priority_ships = [ship for ship in ships_to_place if ship.type in priority_types]
        regular_ships = [ship for ship in ships_to_place if ship.type not in priority_types]
        
        # Создаем список всех возможных позиций
        all_positions = [(x, y) for x in range(GRID_WIDTH) for y in row_range]
        
        # Перемешиваем позиции
        random.shuffle(all_positions)
        
        # Сначала размещаем приоритетные корабли
        for ship in priority_ships:
            # Ищем свободную позицию
            for pos in all_positions:
                x, y = pos
                if self.board[x][y] is None:
                    # Размещаем корабль
                    self.board[x][y] = ship
                    ship.position = (x, y)
                    
                    # Удаляем позицию из списка доступных
                    all_positions.remove(pos)
                    
                    # Перемещаем корабль из неразмещенных в размещенные
                    if self.current_player == 1:
                        self.player1_ships.append(ship)
                        if ship in self.unplaced_ships_player1:
                            self.unplaced_ships_player1.remove(ship)
                    else:
                        self.player2_ships.append(ship)
                        if ship in self.unplaced_ships_player2:
                            self.unplaced_ships_player2.remove(ship)
                    
                    break
        
        # Затем размещаем обычные корабли
        for ship in regular_ships:
            # Ищем свободную позицию
            for pos in all_positions:
                x, y = pos
                if self.board[x][y] is None:
                    # Размещаем корабль
                    self.board[x][y] = ship
                    ship.position = (x, y)
                    
                    # Удаляем позицию из списка доступных
                    all_positions.remove(pos)
                    
                    # Перемещаем корабль из неразмещенных в размещенные
                    if self.current_player == 1:
                        self.player1_ships.append(ship)
                        if ship in self.unplaced_ships_player1:
                            self.unplaced_ships_player1.remove(ship)
                    else:
                        self.player2_ships.append(ship)
                        if ship in self.unplaced_ships_player2:
                            self.unplaced_ships_player2.remove(ship)
                    
                    break
                
        # Проверяем, все ли корабли размещены
        if self.current_player == 1 and not self.unplaced_ships_player1:
            self.setup_complete = True
            self.setup_message = "Нажмите ПРОБЕЛ, чтобы передать ход другому игроку"
        elif self.current_player == 2 and not self.unplaced_ships_player2:
            self.setup_complete = True
            self.setup_message = "Нажмите ПРОБЕЛ, чтобы начать игру"

    def get_menu_position(self, idx, player):
        menu_ship_size = int(MENU_SHIP_SIZE * self.scale_factor)
        menu_spacing = int(MENU_SPACING * self.scale_factor)
        row = idx // SHIPS_PER_ROW
        col = idx % SHIPS_PER_ROW
        menu_width = SHIPS_PER_ROW * (menu_ship_size + menu_spacing)
        menu_offset_x = int(MENU_OFFSET_X * self.scale_factor)
        menu_start_x = ((self.screen.get_width() - menu_width) // 2) + menu_offset_x
        y_base = int(MENU_TOP_Y * self.scale_factor) if player == 1 else self.screen.get_height() - int(100 * self.scale_factor)
        return (menu_start_x + col * (menu_ship_size + menu_spacing), y_base + row * (menu_ship_size + menu_spacing))

    def can_move(self, ship, new_position, required_neighbor_type=None):
        if not self.is_valid_position(new_position):
            return False
        if self.board[new_position[0]][new_position[1]] is not None:
            return False
        if required_neighbor_type:
            if not find_neighbors(self.board, *ship.position, ship_type=required_neighbor_type, player=ship.player):
                return False
            if not find_neighbors(self.board, *new_position, ship_type=required_neighbor_type, player=ship.player):
                return False
        return True

    def draw_highlight(self, cells, color):
        for cell in cells:
            rect = pygame.Rect(self.margin_x + cell[0] * self.cell_size + 2,
                               self.margin_y + cell[1] * self.cell_size + 2,
                               self.cell_size - 4, self.cell_size - 4)
            overlay = pygame.Surface((self.cell_size - 4, self.cell_size - 4), pygame.SRCALPHA)
            overlay.fill((*color, 128))
            self.screen.blit(overlay, rect.topleft)

    def start_pause(self, pause_type):
        # pause_type: 'long' (3 мин) или 'short' (1 мин)
        if self.pause_active:
            return
        duration = 180 if pause_type == "long" else 60
        self.pause_active = True
        self.pause_type = pause_type
        self.pause_owner = self.current_player
        self.pause_end_time = time.time() + duration
        self.pauses[self.current_player][pause_type] -= 1
        # Сохраняем паузу в Firebase
        if self.online_session:
            self.online_session.update_state({"pause": {"active": True, "type": pause_type, "owner": self.current_player, "end": self.pause_end_time}})

    def tick_timers(self):
        now = time.time()
        dt = now - self.last_tick
        self.last_tick = now
        # Если пауза активна — не тикаем таймеры
        if self.pause_active:
            if time.time() >= self.pause_end_time:
                self.pause_active = False
                self.pause_type = None
                self.pause_owner = None
                self.pause_end_time = None
                # Сохраняем снятие паузы в Firebase
                if self.online_session:
                    self.online_session.update_state({"pause": {"active": False}})
            return
        # === Фаза расстановки ===
        if self.phase == 'setup' and not self.setup_complete:
            self.setup_time[self.current_player] -= dt
            if self.setup_time[self.current_player] <= 0:
                self.game_over(3 - self.current_player)
        # === Фаза игры ===
        elif self.phase == 'game':
            self.current_move_timer -= dt
            if self.current_move_timer <= 0:
                # Списываем 30 сек из общего времени
                self.total_time[self.current_player] -= self.move_time
                self.current_move_timer = self.move_time
                if self.total_time[self.current_player] <= 0:
                    self.game_over(3 - self.current_player)
        # ... existing code ...

    def is_flipped(self):
        # Для онлайн-игры: если я игрок 2, переворачиваем поле
        if self.online_session and self.my_login and self.opponent_login:
            return (self.my_login > self.opponent_login)
        return False

    def transform_coords(self, x, y):
        if self.is_flipped():
            return (x, GRID_HEIGHT - 1 - y)
        return (x, y)

    def inverse_transform_coords(self, x, y):
        if self.is_flipped():
            return (x, GRID_HEIGHT - 1 - y)
        return (x, y)

# === Firebase config ===
FIREBASE_API_KEY = "AIzaSyC7yLpkZgHLFMuWDyd-9lRROoKsVCHZ0gk"  # <-- ВСТАВЬТЕ СЮДА СВОЙ КЛЮЧ

def firebase_register(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def firebase_login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        return {"error": str(e)}

class LoginScreen:
    def __init__(self, screen):
        self.screen = screen
        self.email = ""
        self.password = ""
        self.gamelogin = ""
        self.active_field = "email"  # email, password, gamelogin
        self.error = ""
        self.success = False
        self.token = None
        self.mode = "login"  # or "register"
        self.font = pygame.font.Font(None, 32)
        self.clock = pygame.time.Clock()

    def draw(self):
        self.screen.fill((245,245,255))
        font = pygame.font.Font(None, 26)
        small_font = pygame.font.Font(None, 20)
        screen_w, screen_h = self.screen.get_size()
        # Центрирование
        box_width = 280
        box_inner_pad = 8
        max_width = box_width - 2*box_inner_pad - 10
        center_x = screen_w // 2
        # Заголовок
        title = font.render("Регистрация / Вход", True, (30,30,60))
        self.screen.blit(title, (center_x - title.get_width()//2, 40))
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Поля
        fields = [
            ("email", "Email", self.email),
            ("password", "Пароль", "*"*len(self.password)),
            ("gamelogin", "Игровой логин", self.gamelogin)
        ]
        y0 = 110
        y_step = 70
        for i, (name, placeholder, value) in enumerate(fields):
            y = y0 + i*y_step
            box = pygame.Rect(center_x - box_width//2, y, box_width, 40)
            is_active = (self.active_field == name)
            # Подсветка
            if is_active:
                pygame.draw.rect(self.screen, (180,210,255), box, border_radius=8)
                pygame.draw.rect(self.screen, (60,120,255), box, 2, border_radius=8)
            else:
                pygame.draw.rect(self.screen, (230,230,230), box, border_radius=8)
                pygame.draw.rect(self.screen, (180,180,180), box, 2, border_radius=8)
            # Обрезка текста по ширине (с учётом курсора)
            display_value = value
            show_cursor = is_active and (pygame.time.get_ticks()//500)%2 == 0
            cursor = '|' if show_cursor else ''
            while font.size(display_value + (cursor if is_active else ''))[0] > max_width and display_value:
                display_value = display_value[1:]
            if display_value != value:
                display_value = '…' + display_value
            # Placeholder
            if not value and not is_active:
                ph = font.render(placeholder, True, (180,180,180))
                self.screen.blit(ph, (box.x+box_inner_pad, box.y+8))
            else:
                text = display_value + (cursor if is_active else '')
                txt = font.render(text, True, (0,0,0))
                self.screen.blit(txt, (box.x+box_inner_pad, box.y+8))
            # Лейбл — над полем, по центру
            label = small_font.render(placeholder+':', True, (30,30,60))
            self.screen.blit(label, (center_x - label.get_width()//2, box.y-22))
        # Кнопки — на одной линии, по центру
        btn_width = 160
        btn_height = 48
        btn_gap = 24
        btn_y = y0 + len(fields)*y_step + 10
        login_btn = pygame.Rect(center_x - btn_width - btn_gap//2, btn_y, btn_width, btn_height)
        reg_btn = pygame.Rect(center_x + btn_gap//2, btn_y, btn_width, btn_height)
        hovered_login = login_btn.collidepoint(mouse_x, mouse_y)
        hovered_reg = reg_btn.collidepoint(mouse_x, mouse_y)
        pygame.draw.rect(self.screen, (120,220,120) if hovered_login else (100,200,100), login_btn, border_radius=12)
        pygame.draw.rect(self.screen, (120,120,220) if hovered_reg else (100,100,200), reg_btn, border_radius=12)
        # Кнопки — одинаковый уменьшенный шрифт, по центру
        btn_font = pygame.font.Font(None, 18)
        login_render = btn_font.render("Войти", True, (0,0,0))
        login_rect = login_render.get_rect(center=login_btn.center)
        self.screen.blit(login_render, login_rect)
        reg_text = "Зарегистрироваться"
        reg_render = btn_font.render(reg_text, True, (0,0,0))
        reg_rect = reg_render.get_rect(center=reg_btn.center)
        self.screen.blit(reg_render, reg_rect)
        # Ошибка — по центру под кнопками
        if self.error:
            err_icon = font.render("!", True, (255,0,0))
            err = font.render(self.error, True, (255,0,0))
            err_x = center_x - (err_icon.get_width() + 8 + err.get_width())//2
            self.screen.blit(err_icon, (err_x, btn_y+btn_height+18))
            self.screen.blit(err, (err_x+err_icon.get_width()+8, btn_y+btn_height+18))
        pygame.display.flip()

    def run(self):
        font = pygame.font.Font(None, 26)
        screen_w, screen_h = self.screen.get_size()
        box_width = 280
        y0 = 110
        y_step = 70
        center_x = screen_w // 2
        btn_width = 160
        btn_height = 48
        btn_gap = 24
        btn_y = y0 + 3*y_step + 10
        while not self.success:
            # Кнопки вычисляем заранее, чтобы использовать в обработке событий
            login_btn = pygame.Rect(center_x - btn_width - btn_gap//2, btn_y, btn_width, btn_height)
            reg_btn = pygame.Rect(center_x + btn_gap//2, btn_y, btn_width, btn_height)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_TAB:
                        if self.active_field == "email":
                            self.active_field = "password"
                        elif self.active_field == "password":
                            self.active_field = "gamelogin"
                        else:
                            self.active_field = "email"
                    elif event.key == pygame.K_RETURN:
                        self.submit()
                    elif event.key == pygame.K_BACKSPACE:
                        if self.active_field == "email":
                            self.email = self.email[:-1]
                        elif self.active_field == "password":
                            self.password = self.password[:-1]
                        elif self.active_field == "gamelogin":
                            self.gamelogin = self.gamelogin[:-1]
                    else:
                        char = event.unicode
                        if self.active_field == "email" and len(self.email) < 40:
                            self.email += char
                        elif self.active_field == "password" and len(self.password) < 40:
                            self.password += char
                        elif self.active_field == "gamelogin" and len(self.gamelogin) < 20:
                            self.gamelogin += char
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if login_btn.collidepoint(x, y):
                        self.mode = "login"
                        self.submit()
                    elif reg_btn.collidepoint(x, y):
                        self.mode = "register"
                        self.submit()
                    for i, (name, _, _) in enumerate([
                        ("email", "Email", self.email),
                        ("password", "Пароль", self.password),
                        ("gamelogin", "Игровой логин", self.gamelogin)
                    ]):
                        y_box = y0 + i*y_step
                        box = pygame.Rect(center_x - box_width//2, y_box, box_width, 40)
                        if box.collidepoint(x, y):
                            self.active_field = name
            self.draw()
            self.clock.tick(30)

    def submit(self):
        if not self.email or not self.password or not self.gamelogin:
            self.error = "Заполните все поля!"
            return
        if self.mode == "register":
            resp = firebase_register(self.email, self.password)
            if "error" in resp:
                self.error = resp["error"].get("message", str(resp["error"])) if isinstance(resp["error"], dict) else str(resp["error"])
            elif "idToken" in resp:
                self.success = True
                self.token = resp["idToken"]
                self.error = ""
            else:
                self.error = str(resp)
        else:
            resp = firebase_login(self.email, self.password)
            if "error" in resp:
                self.error = resp["error"].get("message", str(resp["error"])) if isinstance(resp["error"], dict) else str(resp["error"])
            elif "idToken" in resp:
                self.success = True
                self.token = resp["idToken"]
                self.error = ""
            else:
                self.error = str(resp)

class MatchmakingScreen:
    def __init__(self, screen, user_login, user_token):
        self.screen = screen
        self.user_login = user_login
        self.user_token = user_token
        self.mode = None  # 'queue' or 'friend'
        self.friend_login = ""
        self.active_field = False
        self.status = ""
        self.font = pygame.font.Font(None, 32)
        self.clock = pygame.time.Clock()
        self.done = False
        self.opponent = None
        self.firebase_url = "https://pygame-56ee7-default-rtdb.europe-west1.firebasedatabase.app"
        self.pending_invite = None
        self._invite_thread = None
        self._invite_thread_stop = False

    def start_invite_checker(self):
        def checker():
            import time
            while not self._invite_thread_stop:
                try:
                    resp = requests.get(f"{self.firebase_url}/invites/{self.user_login}.json", timeout=2)
                    if resp.status_code == 200 and resp.json():
                        data = resp.json()
                        if data.get("status") == "pending":
                            self.pending_invite = data
                    time.sleep(0.7)
                except Exception:
                    time.sleep(1)
        self._invite_thread_stop = False
        self._invite_thread = threading.Thread(target=checker, daemon=True)
        self._invite_thread.start()

    def stop_invite_checker(self):
        self._invite_thread_stop = True
        if self._invite_thread:
            self._invite_thread.join(timeout=1)
        self._invite_thread = None

    def draw(self):
        self.screen.fill((245,245,255))
        font = self.font
        small_font = pygame.font.Font(None, 20)
        screen_w, screen_h = self.screen.get_size()
        box_width = 180
        box_inner_pad = 8
        max_width = box_width - 2*box_inner_pad - 10
        center_x = screen_w // 2
        # Заголовок
        title = font.render("Выберите режим игры", True, (30,30,60))
        self.screen.blit(title, (60, 40))
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # Кнопка 'Найти случайного соперника'
        queue_btn = pygame.Rect(60, 100, 340, 54)
        hovered = queue_btn.collidepoint(mouse_x, mouse_y)
        pygame.draw.rect(self.screen, (120,220,120) if hovered else (100,200,100), queue_btn, border_radius=12)
        self.screen.blit(self.font.render("Найти случайного соперника", True, (0,0,0)), (queue_btn.x+20, queue_btn.y+12))
        # Кнопка 'Сразиться с другом'
        friend_btn = pygame.Rect(60, 170, 340, 54)
        hovered = friend_btn.collidepoint(mouse_x, mouse_y)
        pygame.draw.rect(self.screen, (120,120,220) if hovered else (100,100,200), friend_btn, border_radius=12)
        self.screen.blit(self.font.render("Сразиться с другом", True, (0,0,0)), (friend_btn.x+20, friend_btn.y+12))
        # Кнопка 'Статистика'
        stat_btn = pygame.Rect(60, 240, 340, 54)
        hovered = stat_btn.collidepoint(mouse_x, mouse_y)
        pygame.draw.rect(self.screen, (220,220,220) if hovered else (200,200,200), stat_btn, border_radius=12)
        self.screen.blit(self.font.render("Статистика", True, (0,0,0)), (stat_btn.x+20, stat_btn.y+12))
        # Поле для логина друга
        login_label = font.render("Логин друга:", True, (30,30,60))
        self.screen.blit(login_label, (60, 320))
        login_box = pygame.Rect(220, 320, box_width, 40)
        # Подсветка активного поля
        if self.active_field:
            pygame.draw.rect(self.screen, (180,210,255), login_box, border_radius=8)
            pygame.draw.rect(self.screen, (60,120,255), login_box, 2, border_radius=8)
        else:
            pygame.draw.rect(self.screen, (230,230,230), login_box, border_radius=8)
            pygame.draw.rect(self.screen, (180,180,180), login_box, 2, border_radius=8)
        # Ограничение длины текста
        display_login = self.friend_login
        show_cursor = self.active_field and (pygame.time.get_ticks()//500)%2 == 0
        cursor = '|' if show_cursor else ''
        while font.size(display_login + (cursor if self.active_field else ''))[0] > max_width and display_login:
            display_login = display_login[1:]
        if display_login != self.friend_login:
            display_login = '…' + display_login
        # Placeholder
        if not self.friend_login and not self.active_field:
            placeholder = "Логин друга..."
            ph = placeholder
            while font.size(ph)[0] > max_width and len(ph) > 1:
                ph = ph[1:]
            if ph != placeholder:
                ph = '…' + ph
            ph_render = font.render(ph, True, (180,180,180))
            self.screen.blit(ph_render, (login_box.x+box_inner_pad, login_box.y+8))
        else:
            text = display_login + (cursor if self.active_field else '')
            login_text = font.render(text, True, (0,0,0))
            self.screen.blit(login_text, (login_box.x+box_inner_pad, login_box.y+8))
        # Статус
        if self.status:
            status_text = font.render(self.status, True, (200,40,40))
            self.screen.blit(status_text, (60, 390))
        pygame.display.flip()

    def run(self):
        self.start_invite_checker()
        try:
            while not self.done:
                self.clock.tick(30)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.stop_invite_checker()
                        pygame.quit(); sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos
                        if 40 <= x <= 360 and 80 <= y <= 130:
                            self.mode = 'queue'
                            self.status = "Поиск соперника..."
                            self.draw()
                            self.stop_invite_checker()
                            self.find_opponent_queue()
                            return
                        elif 40 <= x <= 360 and 150 <= y <= 200:
                            self.mode = 'friend'
                            self.status = "Введите логин друга и нажмите Enter"
                            self.active_field = True
                        elif 40 <= x <= 360 and 220 <= y <= 270:
                            # Статистика
                            stat_screen = StatisticsScreen(self.screen, self.user_login)
                            stat_screen.run()
                            self.status = None
                            self.draw()
                        elif 200 <= x <= 360 and 320 <= y <= 360:
                            self.active_field = True
                    if event.type == pygame.KEYDOWN and self.active_field:
                        if event.key == pygame.K_RETURN:
                            if self.mode == 'friend' and self.friend_login:
                                # Отправляем приглашение
                                requests.put(f"{self.firebase_url}/invites/{self.friend_login}.json", json={"from": self.user_login, "status": "pending"})
                                # Ожидание ответа
                                self.stop_invite_checker()
                                wait_screen = InviteWaitScreen(self.screen, self.user_login, self.friend_login, self.firebase_url)
                                wait_screen.run()
                                if wait_screen.accepted:
                                    self.opponent = self.friend_login
                                    self.status = f"{self.friend_login} принял приглашение!"
                                    self.done = True
                                else:
                                    self.status = f"{self.friend_login} не принял приглашение."
                                    self.friend_login = ""
                                    self.mode = None
                                    self.active_field = False
                                self.start_invite_checker()
                            else:
                                self.status = "Введите логин друга!"
                        elif event.key == pygame.K_BACKSPACE:
                            self.friend_login = self.friend_login[:-1]
                        else:
                            char = event.unicode
                            if len(self.friend_login) < 20:
                                self.friend_login += char
                # Проверяем, не пришло ли приглашение этому пользователю (через поток)
                if self.mode != 'friend' and self.pending_invite:
                    data = self.pending_invite
                    self.pending_invite = None
                    receive_screen = InviteReceiveScreen(self.screen, self.user_login, self.firebase_url)
                    receive_screen.run()
                    if receive_screen.accepted:
                        self.opponent = data.get("from")
                        self.status = f"Вы приняли приглашение от {self.opponent}!"
                        self.done = True
                    else:
                        self.status = f"Вы отклонили приглашение от {data.get('from')}"
                        self.mode = None
                        self.active_field = False
                self.draw()
                self.clock.tick(30)
        finally:
            self.stop_invite_checker()

    def find_opponent_queue(self):
        # Добавляем себя в очередь
        requests.put(f"{self.firebase_url}/queue/{self.user_login}.json", json={"login": self.user_login, "status": "waiting"})
        self.status = "Ожидание соперника..."
        self.draw()
        found = False
        start_time = time.time()
        while not found:
            # Получаем всю очередь
            resp = requests.get(f"{self.firebase_url}/queue.json")
            if resp.status_code == 200 and resp.json():
                queue = resp.json()
                for login, data in queue.items():
                    if login != self.user_login and data.get("status") == "waiting":
                        # Нашли соперника
                        self.opponent = login
                        # Удаляем себя и соперника из очереди
                        requests.delete(f"{self.firebase_url}/queue/{self.user_login}.json")
                        requests.delete(f"{self.firebase_url}/queue/{login}.json")
                        self.status = f"Соперник найден: {login}"
                        self.draw()
                        self.clock.tick(10)
                        self.done = True
                        found = True
                        break
            # Если ждем слишком долго — можно выйти
            if time.time() - start_time > 60:
                self.status = "Не удалось найти соперника. Попробуйте позже."
                requests.delete(f"{self.firebase_url}/queue/{self.user_login}.json")
                self.draw()
                self.clock.tick(10)
                self.done = True
                break
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    requests.delete(f"{self.firebase_url}/queue/{self.user_login}.json")
                    pygame.quit(); sys.exit()
            self.status = "Ожидание соперника..."
            self.draw()
            self.clock.tick(10)

class InviteWaitScreen:
    def __init__(self, screen, user_login, friend_login, firebase_url):
        self.screen = screen
        self.user_login = user_login
        self.friend_login = friend_login
        self.firebase_url = firebase_url
        self.font = pygame.font.Font(None, 32)
        self.clock = pygame.time.Clock()
        self.status = f"Ожидание ответа от {friend_login}..."
        self.done = False
        self.accepted = False

    def draw(self):
        self.screen.fill((255,255,255))
        title = self.font.render(self.status, True, (0,0,0))
        self.screen.blit(title, (40, 100))
        pygame.display.flip()

    def run(self):
        start_time = time.time()
        while not self.done:
            # Проверяем статус приглашения
            resp = requests.get(f"{self.firebase_url}/invites/{self.friend_login}.json")
            if resp.status_code == 200 and resp.json():
                data = resp.json()
                if data.get("from") == self.user_login:
                    if data.get("status") == "accepted":
                        self.status = f"{self.friend_login} принял приглашение!"
                        self.accepted = True
                        self.done = True
                    elif data.get("status") == "declined":
                        self.status = f"{self.friend_login} отклонил приглашение."
                        self.accepted = False
                        self.done = True
            if time.time() - start_time > 60:
                self.status = "Время ожидания истекло."
                self.done = True
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
            time.sleep(2)
        # Удаляем приглашение
        requests.delete(f"{self.firebase_url}/invites/{self.friend_login}.json")
        self.draw()
        time.sleep(1)

class InviteReceiveScreen:
    def __init__(self, screen, user_login, firebase_url):
        self.screen = screen
        self.user_login = user_login
        self.firebase_url = firebase_url
        self.font = pygame.font.Font(None, 32)
        self.clock = pygame.time.Clock()
        self.invite_from = None
        self.status = ""
        self.done = False
        self.accepted = False

    def draw(self):
        self.screen.fill((255,255,255))
        if self.invite_from:
            title = self.font.render(f"Вас приглашает {self.invite_from}", True, (0,0,0))
            self.screen.blit(title, (40, 100))
            accept_btn = pygame.Rect(40, 180, 120, 50)
            decline_btn = pygame.Rect(200, 180, 120, 50)
            pygame.draw.rect(self.screen, (100,200,100), accept_btn)
            pygame.draw.rect(self.screen, (200,100,100), decline_btn)
            self.screen.blit(self.font.render("Принять", True, (0,0,0)), (accept_btn.x+10, accept_btn.y+10))
            self.screen.blit(self.font.render("Отклонить", True, (0,0,0)), (decline_btn.x+10, decline_btn.y+10))
        else:
            title = self.font.render("Ожидание приглашения...", True, (0,0,0))
            self.screen.blit(title, (40, 100))
        if self.status:
            status_text = self.font.render(self.status, True, (255,0,0))
            self.screen.blit(status_text, (40, 260))
        pygame.display.flip()

    def run(self):
        start_time = time.time()
        while not self.done:
            # Проверяем наличие приглашения
            resp = requests.get(f"{self.firebase_url}/invites/{self.user_login}.json")
            if resp.status_code == 200 and resp.json():
                data = resp.json()
                self.invite_from = data.get("from")
                if data.get("status") == "pending":
                    self.draw()
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit(); sys.exit()
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            x, y = event.pos
                            if 40 <= x <= 160 and 180 <= y <= 230:
                                # Принять
                                requests.patch(f"{self.firebase_url}/invites/{self.user_login}.json", json={"status": "accepted"})
                                self.status = "Приглашение принято!"
                                self.accepted = True
                                self.done = True
                            elif 200 <= x <= 320 and 180 <= y <= 230:
                                # Отклонить
                                requests.patch(f"{self.firebase_url}/invites/{self.user_login}.json", json={"status": "declined"})
                                self.status = "Приглашение отклонено."
                                self.accepted = False
                                self.done = True
                    continue
            else:
                self.invite_from = None
            if time.time() - start_time > 60:
                self.status = "Время ожидания истекло."
                self.done = True
            self.draw()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
            time.sleep(2)
        # Удаляем приглашение
        requests.delete(f"{self.firebase_url}/invites/{self.user_login}.json")
        self.draw()
        time.sleep(1)

class OnlineGameSession:
    def __init__(self, firebase_url, game_id, player_login, opponent_login):
        self.firebase_url = firebase_url
        self.game_id = game_id
        self.player_login = player_login
        self.opponent_login = opponent_login
        self.state = None
        self.last_update = 0

    def create_session(self, initial_state):
        # initial_state: dict (например, {'turn': 'player1', ...})
        requests.put(f"{self.firebase_url}/games/{self.game_id}.json", json=initial_state)

    def update_state(self, state):
        requests.patch(f"{self.firebase_url}/games/{self.game_id}.json", json=state)

    def get_state(self):
        resp = requests.get(f"{self.firebase_url}/games/{self.game_id}.json")
        if resp.status_code == 200:
            return resp.json()
        return None

    def delete_session(self):
        requests.delete(f"{self.firebase_url}/games/{self.game_id}.json")

class StatisticsScreen:
    def __init__(self, screen, user_login):
        self.screen = screen
        self.user_login = user_login
        self.font = pygame.font.Font(None, 32)
        self.clock = pygame.time.Clock()
        self.done = False

    def draw(self):
        self.screen.fill((255,255,255))
        title = self.font.render("Статистика игрока:", True, (0,0,0))
        self.screen.blit(title, (40, 30))
        stat = self.font.render("Здесь будет ваша статистика", True, (80,80,80))
        self.screen.blit(stat, (40, 90))
        back_btn = pygame.Rect(40, 200, 120, 40)
        pygame.draw.rect(self.screen, (180,180,180), back_btn)
        self.screen.blit(self.font.render("Назад", True, (0,0,0)), (back_btn.x+20, back_btn.y+8))
        pygame.display.flip()

    def run(self):
        while not self.done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    if 40 <= x <= 160 and 200 <= y <= 240:
                        self.done = True
            self.draw()
            self.clock.tick(30)

if __name__ == "__main__":
    print("PYGBAG MAIN STARTED")
    pygame.init()
    # info = pygame.display.Info()
    # window_size = min(WINDOW_SIZE, info.current_h - 60, info.current_w - 40)
    # screen = pygame.display.set_mode((window_size, window_size))
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    login = LoginScreen(screen)
    login.run()
    # После успешного входа запускаем экран выбора режима
    matchmaking = MatchmakingScreen(screen, login.gamelogin, login.token)
    matchmaking.run()
    # --- ONLINE SESSION LOGIC ---
    firebase_url = "https://pygame-56ee7-default-rtdb.europe-west1.firebasedatabase.app"
    my_login = login.gamelogin
    opponent_login = matchmaking.opponent
    if opponent_login:
        # Формируем уникальный game_id (оба игрока получат одинаковый id)
        logins = sorted([my_login, opponent_login])
        game_id = f"{logins[0]}_{logins[1]}"
        online_session = OnlineGameSession(firebase_url, game_id, my_login, opponent_login)
        # Если мы инициатор — создаём сессию
        if my_login < opponent_login:
            online_session.create_session({"turn": my_login, "state": "setup"})
        # Передаём online_session в Game
        game = Game(online_session=online_session, my_login=my_login, opponent_login=opponent_login)
    else:
        game = Game()
    game.run()