import pygame
import json
import math
from simulator import Simulator
from data import *
from algorithms import *
from utils import *
from uis import *
from drawer_render import DrawerRenderer
from drawer_ui import DrawerUI

class Drawer:
    def __init__(self, simulator: Simulator, width=1920, height=1080):
        pygame.init()
        
        self.simulator = simulator  # 시뮬레이터 객체(순수 로직)
        
        # 화면 설정
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("전력 시뮬레이터(노드이동파티클 + 시나리오GUI 분리버전)")
        
        # 폰트
        self.font = pygame.font.SysFont("malgungothic", 24, bold=True)
        self.big_font = pygame.font.SysFont("malgungothic", 48, bold=True)
        self.small_font = pygame.font.SysFont("malgungothic", 20, bold=True)
        self.scenario_name_font = pygame.font.SysFont("malgungothic", 28, bold=True)
        
        # UI 패널
        self.panel_width = 380
        self.ui_rect = pygame.Rect(self.width - self.panel_width, 0, self.panel_width, self.height)
        
        # 파티클 시스템(시각화)
        self.particles = ParticleSystem()
        
        # UI/이벤트 관련
        self.dragging_bldg = None
        self.drag_offset = (0,0)
        self.frame_count = 0
        self.add_mode = "none"
        self.temp_line_start = None
        self.show_help = False
        self.hover_bldg = None
        self.hover_line = None
        
        # Waypoint 편집 관련
        self.editing_line = None  # 현재 편집 중인 송전선
        self.temp_waypoints = []  # 임시 waypoint 리스트
        self.waypoint_mode = False  # waypoint 편집 모드
        self.dragging_waypoint = False  # waypoint 드래그 상태
        self.dragging_waypoint_index = -1  # 드래그 중인 waypoint 인덱스
        
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.5  # 초기 확대
        
        self.dragging_background = False
        self.old_offset = (0,0)
        self.drag_start = (0,0)
        
        self.buttons = []
        
        self.force_layout_on_drag = True
        self.running = True
        
        # 시나리오 목록, 패널
        self.show_scenario_list = False
        self.scenario_scroll = 0
        
        # 컨텍스트 메뉴
        self.context_menu = ContextMenu(self.simulator, self)
        
        # 이전 step에서의 라인 flow
        self.prev_flows = {}
        
        self.clock = pygame.time.Clock()
        
        # 렌더러와 UI 모듈 초기화
        self.renderer = DrawerRenderer(self)
        self.ui = DrawerUI(self)
        
        # AI 업그레이드 패널 관련
        self.show_ai_upgrade_panel = False
        self.ai_upgrade_option_buttons = []
        
        # 버튼 설정
        self.ui.setup_buttons()
    
    def set_mode(self, mode):
        """모드 변경 (normal, delete 등)"""
        if mode == "normal":
            self.add_mode = "none"
            self.temp_line_start = None
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        elif mode == "delete":
            self.add_mode = "delete"
            self.temp_line_start = None
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_NO)
    
    def save_current_state(self):
        data = {}
        data["buildings"] = []
        for b in self.simulator.city.buildings:
            info = {
                "base_supply": b.base_supply,
                "solar_capacity": b.solar_capacity,
                "x": b.x,
                "y": b.y,
                "removed": b.removed
            }
            data["buildings"].append(info)
        data["lines"] = []
        for pl in self.simulator.city.lines:
            linfo = {
                "u": pl.u,
                "v": pl.v,
                "capacity": pl.capacity,
                "cost": pl.cost,
                "removed": pl.removed
            }
            data["lines"].append(linfo)
        data["budget"] = self.simulator.budget
        data["money"] = self.simulator.money
        data["event_count"] = self.simulator.event_count
        data["simTime"] = self.simulator.simTime.isoformat()
        
        fname = "output_save.json"
        with open(fname, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("[저장 완료]", fname)
    
    def run(self):
        while self.running:
            dt = self.clock.tick(30)
            # 이벤트 처리
            self.ui.handle_events()
            
            # 시뮬레이터 로직 업데이트
            self.simulator.update_sim_time(dt)
            self.simulator.apply_demand_pattern()
            self.simulator.update_events()
            self.simulator.update_flow(instant=True)
            
            # 파티클 업데이트
            self.particles.update(dt)
            
            # 프레임 카운트 증가
            self.frame_count += 1
            
            # 화면 그리기
            self.renderer.draw_frame()
            pygame.display.flip()
        
        pygame.quit()
    
    def screen_to_world(self, sx, sy):
        wx = (sx - self.offset_x) / self.scale
        wy = (sy - self.offset_y) / self.scale
        return (wx, wy)
    
    def world_to_screen(self, wx, wy):
        sx = wx * self.scale + self.offset_x
        sy = wy * self.scale + self.offset_y
        return (sx, sy)
    
    def zoom(self, mpos, factor):
        mx, my = mpos
        before = self.screen_to_world(mx, my)
        self.scale *= factor
        after = self.screen_to_world(mx, my)
        self.offset_x += (after[0] - before[0]) * self.scale
        self.offset_y += (after[1] - before[1]) * self.scale
    
    def track_flow_changes(self):
        """라인의 flow 변화를 추적"""
        new_flows = {}
        for pl in self.simulator.city.lines:
            if not pl.removed:
                new_flows[pl] = pl.flow
        
        # 제거된 라인 처리
        for pl in list(self.prev_flows.keys()):
            if pl not in new_flows:
                self.prev_flows.pop(pl, None)
        
        # 첫 실행 시 초기화
        if not self.prev_flows:
            self.prev_flows = new_flows
            return
            
        self.prev_flows = new_flows 