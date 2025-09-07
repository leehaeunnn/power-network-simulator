import pygame
import random
from city import *

class Particle:
    """
    - building_start, building_end: Building 객체
    - forward: True면 start->end 방향
    - t: 0~1 보간
    """
    def __init__(self, building_start, building_end, forward, speed):
        self.b_start=building_start
        self.b_end=building_end
        self.forward=forward
        self.speed=speed
        self.t=0.0

    def update(self,dt):
        dsec=dt/1000.0
        self.t+=self.speed*dsec

    def get_world_pos(self):
        if self.t>1:
            # 이미 끝난 파티클
            return (999999,999999)
        x1,y1=self.b_start.x,self.b_start.y
        x2,y2=self.b_end.x,self.b_end.y
        if not self.forward:
            x1,y1,x2,y2=x2,y2,x1,y1
        px=x1+(x2-x1)*self.t
        py=y1+(y2-y1)*self.t
        return (px,py)

class ParticleSystem:
    def __init__(self):
        self.particles=[]

    def update(self,dt):
        dead=[]
        for p in self.particles:
            p.update(dt)
            if p.t>1:
                dead.append(p)
        for d in dead:
            self.particles.remove(d)

    def draw(self,screen,sim):
        for p in self.particles:
            wx,wy=p.get_world_pos()
            if wx>99999:
                continue
            sx,sy=sim.world_to_screen(wx,wy)
            
            # 파티클 색상 설정 (전력 흐름에 따라)
            if p.b_start.base_supply > 0 or p.b_end.base_supply > 0:
                # 발전소가 포함된 경우 밝은 노란색
                color = (255, 255, 100)
            else:
                # 일반 송전선은 연한 노란색
                color = (200, 200, 80)
            
            # 파티클 크기 설정
            size = 4
            
            # 파티클 그리기 (그림자 효과 포함)
            shadow_surf = pygame.Surface((size*2+4, size*2+4), pygame.SRCALPHA)
            pygame.draw.circle(shadow_surf, (*color[:3], 100), (size+2, size+2), size+2)
            screen.blit(shadow_surf, (int(sx)-size-2, int(sy)-size-2))
            
            pygame.draw.circle(screen, color, (int(sx), int(sy)), size)

    def spawn_particles_for_line(self,pl,b_start,b_end,dt):
        if pl.removed:
            return
        if b_start.removed or b_end.removed:
            return
        if pl.capacity<1e-9:
            return
        f=pl.flow
        spawn_rate=0.5*abs(f)  # 유량 크기에 비례
        ratio=0 if pl.capacity<=0 else abs(f)/pl.capacity

        base_speed=0.2
        speed=base_speed+0.5*ratio
        dsec=dt/1000.0
        exp_new=spawn_rate*dsec
        num_new=int(exp_new)
        if random.random()<(exp_new-num_new):
            num_new+=1

        forward=(f>=0)
        for _ in range(num_new):
            part=Particle(b_start,b_end,forward,speed)
            self.particles.append(part)

class Button:
    def __init__(self, rect, text, callback, color=None, active=True, text_color=None):
        self.rect=pygame.Rect(rect)
        self.text=text
        self.callback=callback
        self.hover=False
        self.custom_color = color  # 사용자 지정 색상
        self.active = active  # 버튼 활성화 상태
        self.text_color = text_color # text_color 멤버 변수 추가

    def draw(self, screen, font):
        # 버튼 배경을 간단한 그라디언트로
        rect_surf=pygame.Surface((self.rect.width, self.rect.height))
        
        if self.custom_color:
            # 사용자 지정 색상을 사용하는 경우
            color_top = tuple(min(c + 30, 255) for c in self.custom_color)  # 밝은 색
            if self.hover and self.active:
                color_bottom = tuple(min(c + 50, 255) for c in self.custom_color)  # 호버 시 더 밝은 색
            else:
                color_bottom = self.custom_color
        else:
            # 기본 색상 사용
            color_top = (200, 200, 220)
            if not self.active:
                color_bottom = (150, 150, 170)  # 비활성화 색상
            elif self.hover:
                color_bottom = (150, 150, 255)  # 호버 색상
            else:
                color_bottom = (170, 170, 210)  # 기본 색상
                
        # 그라디언트 적용
        for y in range(self.rect.height):
            alpha = y / float(self.rect.height)
            r = int(color_top[0] * (1-alpha) + color_bottom[0] * alpha)
            g = int(color_top[1] * (1-alpha) + color_bottom[1] * alpha)
            b = int(color_top[2] * (1-alpha) + color_bottom[2] * alpha)
            pygame.draw.line(rect_surf, (r, g, b), (0, y), (self.rect.width, y))
            
        screen.blit(rect_surf, self.rect.topleft)

        # 버튼 테두리
        border_color = (50, 50, 80) if self.active else (100, 100, 120)
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=8)
        
        # 텍스트 색상 (비활성화 시 회색, 사용자 지정 색상 우선)
        final_text_color = self.text_color if self.text_color else ((0, 0, 0) if self.active else (80, 80, 80))
        txt = font.render(self.text, True, final_text_color)
        tr = txt.get_rect(center=self.rect.center)
        screen.blit(txt, tr)

    def check_event(self, event):
        if not self.active:
            return False
            
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hover = self.rect.collidepoint(mx, my)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hover:
                self.callback()
                return True
        return False

class ContextMenu:
    def __init__(self, simulator, drawer):
        self.simulator = simulator
        self.drawer = drawer
        self.visible = False
        self.x = 0
        self.y = 0
        self.target = None
        self.items = []
        self.hover_idx = -1
        
    def show(self, x, y, target):
        self.visible = True
        self.x = x
        self.y = y
        self.target = target
        self.items = self.create_menu_items()
        
    def hide(self):
        self.visible = False
        self.target = None
        self.items = []
        
    def create_menu_items(self):
        items = []
        if not self.target:
            return items
            
        if isinstance(self.target, PowerLine):  # 송전선 메뉴
            items.extend([
                ("경유점 편집", self.edit_waypoints),
                ("경유점 제거", self.clear_waypoints),
                ("---", None),  # 구분선
                ("용량 +10.0", lambda: self.adjust_capacity(10.0)),
                ("용량 +5.0", lambda: self.adjust_capacity(5.0)),
                ("용량 +1.0", lambda: self.adjust_capacity(1.0)),
                ("---", None),  # 구분선
                ("용량 -1.0", lambda: self.adjust_capacity(-1.0)),
                ("용량 -5.0", lambda: self.adjust_capacity(-5.0)),
                ("용량 -10.0", lambda: self.adjust_capacity(-10.0)),
                ("---", None),  # 구분선
                ("삭제", self.delete_line)
            ])
            return items
            
        b = self.target
        if b.base_supply > 0:  # 발전소
            items.extend([
                ("발전량 +10.0", lambda: self.adjust_supply(10.0)),
                ("발전량 +5.0", lambda: self.adjust_supply(5.0)),
                ("발전량 +1.0", lambda: self.adjust_supply(1.0)),
                ("---", None),  # 구분선
                ("발전량 -1.0", lambda: self.adjust_supply(-1.0)),
                ("발전량 -5.0", lambda: self.adjust_supply(-5.0)),
                ("발전량 -10.0", lambda: self.adjust_supply(-10.0))
            ])
        elif b.base_supply < 0:  # 아파트
            items.extend([
                ("수요량 +10.0", lambda: self.adjust_demand(10.0)),
                ("수요량 +5.0", lambda: self.adjust_demand(5.0)),
                ("수요량 +1.0", lambda: self.adjust_demand(1.0)),
                ("---", None),  # 구분선
                ("수요량 -1.0", lambda: self.adjust_demand(-1.0)),
                ("수요량 -5.0", lambda: self.adjust_demand(-5.0)),
                ("수요량 -10.0", lambda: self.adjust_demand(-10.0))
            ])
            
        if b.solar_capacity > 0 or b.base_supply <= 0:  # 태양광 설치 가능
            if len(items) > 0:
                items.append(("---", None))  # 구분선
            items.extend([
                ("태양광 +5.0", lambda: self.adjust_solar(5.0)),
                ("태양광 +1.0", lambda: self.adjust_solar(1.0)),
                ("태양광 -1.0", lambda: self.adjust_solar(-1.0)),
                ("태양광 -5.0", lambda: self.adjust_solar(-5.0))
            ])
        
        # 배터리 관련 메뉴 추가
        if len(items) > 0:
            items.append(("---", None))  # 구분선
            
        # 이미 배터리가 설치된 건물
        if b.battery_capacity > 0:
            items.extend([
                (f"배터리 상태: {b.battery_charge:.1f}/{b.battery_capacity:.1f}", None),  # 정보 표시
                ("배터리 +5.0", lambda: self.adjust_battery(5.0)),
                ("배터리 +1.0", lambda: self.adjust_battery(1.0)),
                ("배터리 -1.0", lambda: self.adjust_battery(-1.0)),
                ("배터리 -5.0", lambda: self.adjust_battery(-5.0)),
                ("배터리 충전", self.charge_battery),
                ("배터리 방전", self.discharge_battery)
            ])
        else:  # 배터리 미설치 건물
            items.extend([
                ("배터리 설치 (5.0)", lambda: self.adjust_battery(5.0)),
                ("배터리 설치 (10.0)", lambda: self.adjust_battery(10.0))
            ])
            
        # 스마트 그리드 연결 메뉴
        items.append(("---", None))
        if b.smart_grid_connected:
            items.append(("스마트 그리드 연결 해제", self.toggle_smart_grid))
        else:
            items.append(("스마트 그리드 연결", self.toggle_smart_grid))
        
        # 건물 유형 변경 메뉴 (아파트인 경우)
        if b.base_supply < 0:
            items.append(("---", None))
            building_types = ["apartment", "office", "school", "hospital", "shopping_mall"]
            current_type = b.building_type if hasattr(b, "building_type") else "apartment"
            
            for btype in building_types:
                if btype != current_type:
                    items.append((f"유형 변경: {btype}", lambda btype=btype: self.change_building_type(btype)))
        
        # 기본 메뉴 항목 (삭제)
        if len(items) > 0:
            items.append(("---", None))
        items.append(("삭제", self.delete_building))
        return items
        
    def adjust_capacity(self, delta):
        if isinstance(self.target, PowerLine):
            self.target.capacity = max(0, self.target.capacity + delta)
            self.simulator.update_flow(True)
        self.hide()
        
    def delete_line(self):
        if isinstance(self.target, PowerLine):
            self.target.removed = True
            self.simulator.update_flow(True)
        self.hide()
        
    def adjust_supply(self, delta):
        if self.target:
            self.target.base_supply += delta
            self.target.current_supply = self.target.base_supply
            self.simulator.update_flow(True)
        self.hide()
        
    def adjust_demand(self, delta):
        if self.target:
            self.target.base_supply -= delta  # 수요는 음수라서 부호 반대
            self.simulator.update_flow(True)
        self.hide()
        
    def adjust_solar(self, delta):
        if self.target:
            self.target.solar_capacity = max(0, self.target.solar_capacity + delta)
            self.simulator.update_flow(True)
        self.hide()
        
    def delete_building(self):
        if self.target:
            self.target.removed = True
            self.simulator.update_flow(True)
        self.hide()
        
    def adjust_battery(self, delta):
        """
        건물의 배터리 용량을 조절합니다.
        """
        if self.target:
            new_capacity = max(0, self.target.battery_capacity + delta)
            
            # 용량이 변경되는 경우에만 처리
            if new_capacity != self.target.battery_capacity:
                if self.target.battery_capacity == 0 and new_capacity > 0:
                    print(f"배터리 신규 설치: {new_capacity:.1f}")
                    # 비용 처리 (시뮬레이터에 예산이 있다면)
                    cost = new_capacity * 2  # 예시 비용 (용량 * 2)
                    if hasattr(self.simulator, 'budget') and self.simulator.budget >= cost:
                        self.simulator.budget -= cost
                        print(f"비용 지불: {cost:.1f} (남은 예산: {self.simulator.budget:.1f})")
                    else:
                        print("예산 부족 또는 예산 시스템 없음")
                else:
                    # 용량 변경
                    capacity_change = new_capacity - self.target.battery_capacity
                    direction = "증가" if capacity_change > 0 else "감소"
                    print(f"배터리 용량 {direction}: {abs(capacity_change):.1f}")
                    
                    # 비용 또는 환불 처리
                    if capacity_change > 0:  # 용량 증가 (추가 비용)
                        cost = capacity_change * 2
                        if hasattr(self.simulator, 'budget') and self.simulator.budget >= cost:
                            self.simulator.budget -= cost
                            print(f"비용 지불: {cost:.1f} (남은 예산: {self.simulator.budget:.1f})")
                        else:
                            print("예산 부족 또는 예산 시스템 없음")
                    else:  # 용량 감소 (일부 환불)
                        refund = abs(capacity_change) * 1  # 감소분의 절반만 환불
                        if hasattr(self.simulator, 'budget'):
                            self.simulator.budget += refund
                            print(f"환불: {refund:.1f} (남은 예산: {self.simulator.budget:.1f})")
                
                # 배터리 용량 설정
                self.target.battery_capacity = new_capacity
                
                # 충전량이 용량을 초과하지 않도록 조정
                if self.target.battery_charge > new_capacity:
                    self.target.battery_charge = new_capacity
                
                # 스마트 그리드 자동 연결 (배터리 설치 시)
                if new_capacity > 0 and not self.target.smart_grid_connected:
                    self.target.smart_grid_connected = True
                    print("스마트 그리드 자동 연결됨")
                
                # 시뮬레이션 업데이트
                self.simulator.update_flow(True)
        self.hide()
    
    def charge_battery(self):
        """
        배터리를 최대치까지 충전합니다. (시뮬레이션 용)
        """
        if self.target and self.target.battery_capacity > 0:
            before_charge = self.target.battery_charge
            self.target.battery_charge = self.target.battery_capacity
            charge_amount = self.target.battery_capacity - before_charge
            print(f"배터리 충전: +{charge_amount:.1f} (최대치)")
            
            # 비용 처리 (옵션)
            if hasattr(self.simulator, 'budget'):
                cost = charge_amount * 0.5  # 예시 비용 (충전량 * 0.5)
                self.simulator.budget -= cost
                print(f"충전 비용: {cost:.1f} (남은 예산: {self.simulator.budget:.1f})")
            
            self.simulator.update_flow(True)
        self.hide()
    
    def discharge_battery(self):
        """
        배터리를 완전히 방전시킵니다. (시뮬레이션 용)
        """
        if self.target and self.target.battery_capacity > 0:
            discharge_amount = self.target.battery_charge
            self.target.battery_charge = 0
            print(f"배터리 방전: -{discharge_amount:.1f} (완전 방전)")
            
            # 환불 처리 (옵션)
            if hasattr(self.simulator, 'budget') and discharge_amount > 0:
                refund = discharge_amount * 0.3  # 예시 환불 (방전량 * 0.3)
                self.simulator.budget += refund
                print(f"방전 환불: {refund:.1f} (남은 예산: {self.simulator.budget:.1f})")
            
            self.simulator.update_flow(True)
        self.hide()
    
    def edit_waypoints(self):
        """송전선 waypoint 편집 모드로 전환"""
        if isinstance(self.target, PowerLine):
            self.drawer.editing_line = self.target
            self.drawer.temp_waypoints = self.target.waypoints.copy()
            self.drawer.waypoint_mode = True
            self.drawer.add_mode = "waypoint"
            print(f"송전선 {self.target.u}-{self.target.v} waypoint 편집 모드 시작")
            print("사용법:")
            print("  • 송전선 위 클릭: 해당 지점에 waypoint 추가")
            print("  • waypoint 드래그: 위치 이동")
            print("  • waypoint 우클릭: 해당 waypoint 삭제")
            print("  • 빈 공간 우클릭: 마지막 waypoint 삭제")
            print("  • Enter: 저장 및 완료")
            print("  • ESC: 취소")
        self.hide()
    
    def clear_waypoints(self):
        """송전선의 모든 waypoint 제거"""
        if isinstance(self.target, PowerLine):
            self.target.clear_waypoints()
            print(f"송전선 {self.target.u}-{self.target.v}의 모든 waypoint 제거됨")
            self.simulator.update_flow(True)
        self.hide()
    
    def toggle_smart_grid(self):
        """
        스마트 그리드 연결/해제를 토글합니다.
        """
        if self.target:
            self.target.smart_grid_connected = not self.target.smart_grid_connected
            state = "연결됨" if self.target.smart_grid_connected else "해제됨"
            print(f"스마트 그리드 {state}")
            
            # 비용 처리 (연결 시에만)
            if self.target.smart_grid_connected and hasattr(self.simulator, 'budget'):
                cost = 2.0  # 스마트 그리드 설치 비용
                self.simulator.budget -= cost
                print(f"스마트그리드 설치비: {cost:.1f} (남은 예산: {self.simulator.budget:.1f})")
            
            self.simulator.update_flow(True)
        self.hide()
    
    def change_building_type(self, new_type):
        """
        건물 유형을 변경합니다.
        """
        if self.target:
            old_type = self.target.building_type if hasattr(self.target, "building_type") else "apartment"
            self.target.building_type = new_type
            print(f"건물 유형 변경: {old_type} → {new_type}")
            
            # 에너지 효율 자동 조정 (건물 유형에 따라)
            if new_type == "hospital":
                self.target.energy_efficiency = 1.2  # 병원은 에너지 효율이 낮음
            elif new_type == "office":
                self.target.energy_efficiency = 1.0  # 사무실은 보통
            elif new_type == "school":
                self.target.energy_efficiency = 0.9  # 학교는 효율 좋음
            
            self.simulator.update_flow(True)
        self.hide()
        
    def draw(self, screen):
        if not self.visible:
            return
            
        # 메뉴 크기 계산
        padding = 10
        item_height = 30
        menu_width = 180  # 메뉴 너비 증가
        
        # 구분선 높이 계산을 포함한 전체 높이 계산
        total_height = padding * 2
        for item in self.items:
            if item[0] == "---":  # 구분선
                total_height += 8  # 구분선 높이
            else:
                total_height += item_height
        
        # 화면 경계 체크 (drawer의 width/height 사용)
        if self.x + menu_width > self.drawer.width:
            self.x = self.drawer.width - menu_width - 5
        if self.y + total_height > self.drawer.height:
            self.y = self.drawer.height - total_height - 5
            
        # 메뉴 배경
        menu_rect = pygame.Rect(self.x, self.y, menu_width, total_height)
        
        # 그림자 효과
        shadow_rect = menu_rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(screen, (0,0,0,50), shadow_rect, border_radius=8)
        
        # 메인 배경
        pygame.draw.rect(screen, (240,240,255), menu_rect, border_radius=8)
        pygame.draw.rect(screen, (100,100,130), menu_rect, 2, border_radius=8)
        
        # 메뉴 아이템
        mx, my = pygame.mouse.get_pos()
        self.hover_idx = -1
        
        current_y = self.y + padding
        for i, (text, callback) in enumerate(self.items):
            if text == "---":  # 구분선
                pygame.draw.line(screen, (180,180,200), 
                               (self.x + 10, current_y + 4),
                               (self.x + menu_width - 10, current_y + 4), 2)
                current_y += 8
                continue
                
            item_rect = pygame.Rect(self.x, current_y, menu_width, item_height)
            
            # 호버 효과
            if item_rect.collidepoint(mx, my):
                self.hover_idx = i
                pygame.draw.rect(screen, (200,200,255), item_rect)
                
            # 텍스트
            text_surf = self.drawer.small_font.render(text, True, (0,0,0))  # drawer의 폰트 사용
            text_rect = text_surf.get_rect(midleft=(item_rect.left + 15, item_rect.centery))
            screen.blit(text_surf, text_rect)
            
            current_y += item_height
            
    def handle_click(self, pos):
        if not self.visible:
            return False
            
        mx, my = pos
        if self.hover_idx >= 0 and self.hover_idx < len(self.items):
            _, callback = self.items[self.hover_idx]
            if callback:  # 구분선이 아닌 경우에만 콜백 실행
                callback()
            return True
            
        # 메뉴 영역 밖 클릭
        menu_rect = pygame.Rect(self.x, self.y, 180, 
                              sum(30 if item[0] != "---" else 8 for item in self.items) + 20)
        if not menu_rect.collidepoint(mx, my):
            self.hide()
            return True
            
        return False

    def draw_tooltip(self):
        """호버 상태의 건물이나 송전선에 대한 툴팁 표시"""
        if not (self.drawer.hover_bldg or self.drawer.hover_line):
            return
        
        lines = []
        if self.drawer.hover_bldg and not self.drawer.hover_bldg.removed:
            # 건물 툴팁
            b = self.drawer.hover_bldg
            lines.append(("● " + b.get_type_str() + f" {b.idx}", (255, 255, 200)))
            
            # 건물 상세 정보 추가 (city.py의 Building.get_detailed_info() 사용 권장)
            if hasattr(b, 'get_detailed_info'):
                detailed_info = b.get_detailed_info()
                for info_text in detailed_info:
                    color = (200, 255, 200)  # 기본 색상
                    if "정전" in info_text: color = (255, 100, 100)
                    elif "태양광" in info_text: color = (255, 255, 150)
                    elif "부족" in info_text or "⚠️" in info_text : color = (255, 150, 150)
                    elif "배터리" in info_text: color = (150, 200, 255)
                    lines.append(("  " + info_text, color))
            else:
                # get_detailed_info 메소드가 없는 경우, 기존 로직을 drawer_render.py와 유사하게 수정
                if b.base_supply < 0: # 소비자 또는 프로슈머(수요 측면)
                    demand = abs(b.base_supply) # UI 표시용 초기 수요
                    lines.append((f"  기본 수요: {demand:.1f}", (200, 255, 200)))

                    if hasattr(b, 'current_supply') and abs(b.current_supply) != demand:
                         lines.append((f"  현재 수요: {abs(b.current_supply):.1f}", (210, 210, 255)))

                    if b.solar_capacity > 0:
                        lines.append((f"  태양광설비: {b.solar_capacity:.1f}", (255, 255, 150)))
                    
                    # 부족량은 b.shortage 값을 직접 사용
                    if hasattr(b, 'shortage') and b.shortage > 1e-9:
                        shortage_color = (255, 150, 150)
                        lines.append((f"  부족: {b.shortage:.1f}", shortage_color))
                        if demand > 1e-9:
                            shortage_ratio = (b.shortage / demand) * 100
                            lines.append((f"  부족률: {shortage_ratio:.1f}%", shortage_color))
                        else:
                            lines.append(("  부족률: -", shortage_color))
                    else: # 부족이 없을 때
                        lines.append(("  공급 상태: 양호", (150, 255, 150)))

                elif b.base_supply > 0: # 순수 생산자
                    lines.append((f"  기본 발전: {b.base_supply:.1f}", (200, 255, 200)))
                    if hasattr(b, 'current_supply') and abs(b.current_supply - b.base_supply) > 1e-9 :
                         lines.append((f"  현재 출력: {b.current_supply:.1f}", (210, 210, 255)))
                    if b.solar_capacity > 0: # 발전소도 태양광 가질 수 있음
                        lines.append((f"  태양광설비: {b.solar_capacity:.1f}", (255, 255, 150)))
                    
                    # 송전량은 b.transmitted_power 사용
                    if hasattr(b, 'transmitted_power'):
                        lines.append((f"  송전량: {b.transmitted_power:.1f}", (200, 255, 200)))
                    else:
                        lines.append(("  송전량: N/A", (200, 200, 200)))
                else: # base_supply == 0
                    lines.append((f"  타입: {b.get_type_str()}", (220, 220, 220)))
                    if b.solar_capacity > 0:
                        lines.append((f"  태양광: {b.solar_capacity:.1f}", (255, 255, 150)))
                        if hasattr(b, 'current_supply'):
                            lines.append((f"  현재출력: {b.current_supply:.1f}", (210, 210, 255)))
                        if hasattr(b, 'transmitted_power'):
                            lines.append((f"  송전량: {b.transmitted_power:.1f}", (200, 255, 200)))


                if b.battery_capacity > 0:
                    charge_percent = 0
                    if b.battery_capacity > 1e-9:
                        charge_percent = (b.battery_charge / b.battery_capacity) * 100
                    lines.append((f"  배터리: {b.battery_charge:.1f}/{b.battery_capacity:.1f} ({charge_percent:.0f}%)", (150, 200, 255)))

                if b.blackout:
                    lines.append(("  ⚠ 정전!", (255, 100, 100)))
