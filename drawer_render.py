import pygame
import math
from utils import *
from data import *
from algorithms import analyze_current_grid_status

class DrawerRenderer:
    def __init__(self, drawer):
        self.drawer = drawer  # Drawer 인스턴스 참조
        self.simulator = drawer.simulator  # 시뮬레이터 참조
        self.screen = drawer.screen  # pygame 화면
        self.width = drawer.width
        self.height = drawer.height
        
        # 폰트 참조
        self.font = drawer.font
        self.big_font = drawer.big_font
        self.small_font = drawer.small_font
        self.scenario_name_font = drawer.scenario_name_font
    
    def _truncate_text(self, text, font, max_width):
        if font.size(text)[0] <= max_width:
            return text
        else:
            truncated_text = ""
            # "..."의 너비를 미리 계산
            ellipsis_width = font.size("...")[0]
            current_width = 0
            for char in text:
                char_width = font.size(char)[0]
                if current_width + char_width + ellipsis_width > max_width:
                    break
                truncated_text += char
                current_width += char_width
            return truncated_text + "..."
    
    def draw_frame(self, partial=False):
        """전체 화면 그리기"""
        # 배경
        draw_city_background(self.screen, self.width, self.height)
        
        # 임시 송전선 그리기 (송전선 추가 모드)
        self._draw_temp_line()
        
        # 송전선 그리기
        self._draw_power_lines()
        
        # 파티클 그리기
        self.drawer.particles.draw(self.screen, self.drawer)
        
        # 건물 그리기
        for b in self.simulator.city.buildings:
            if b.removed:
                continue
            self.draw_building(b)
        
        # UI 패널 그리기
        self._draw_ui_panel()
        
        # 전력 공급 상황 표시
        self._draw_power_status()
        
        # 모드 및 예산 정보 표시
        self._draw_mode_info()
        
        # 시간/날씨 표시
        self._draw_time_weather()
        
        if not partial:
            if self.drawer.show_help:
                self.draw_help_overlay()
            if self.drawer.show_scenario_list:
                self.draw_scenario_list()
            if hasattr(self.drawer, 'show_ai_upgrade_panel') and self.drawer.show_ai_upgrade_panel:
                self.draw_ai_upgrade_panel()
            # 발전소 메뉴 그리기
            if hasattr(self.drawer, 'ui_handler'):
                self.draw_power_plant_menu()
            self.draw_tooltip()
            self.drawer.context_menu.draw(self.screen)

    def _draw_temp_line(self):
        """송전선 추가 모드에서 임시 선 그리기 및 waypoint 편집 표시"""
        if self.drawer.add_mode == "add_line" and self.drawer.temp_line_start:
            mx, my = pygame.mouse.get_pos()
            start_x, start_y = self.drawer.world_to_screen(self.drawer.temp_line_start.x, self.drawer.temp_line_start.y)
            dash_length = 10
            space_length = 5
            total_length = math.hypot(mx-start_x, my-start_y)
            angle = math.atan2(my-start_y, mx-start_x)
            dash_count = int(total_length / (dash_length + space_length))
            for i in range(dash_count):
                start_dist = i * (dash_length + space_length)
                end_dist = start_dist + dash_length
                if end_dist > total_length:
                    end_dist = total_length
                dash_start_x = start_x + math.cos(angle) * start_dist
                dash_start_y = start_y + math.sin(angle) * start_dist
                dash_end_x = start_x + math.cos(angle) * end_dist
                dash_end_y = start_y + math.sin(angle) * end_dist
                pygame.draw.line(self.screen, (255, 255, 100),
                               (dash_start_x, dash_start_y),
                               (dash_end_x, dash_end_y), 2)
        
        # waypoint 편집 모드일 때 임시 waypoint 표시
        elif self.drawer.add_mode == "waypoint" and self.drawer.editing_line:
            # 편집 중인 송전선 강조
            b1 = self.simulator.city.buildings[self.drawer.editing_line.u]
            b2 = self.simulator.city.buildings[self.drawer.editing_line.v]
            sx1, sy1 = self.drawer.world_to_screen(b1.x, b1.y)
            sx2, sy2 = self.drawer.world_to_screen(b2.x, b2.y)
            
            # 임시 waypoint를 포함하여 선 그리기
            points = [(sx1, sy1)]
            for wp_x, wp_y in self.drawer.temp_waypoints:
                wp_sx, wp_sy = self.drawer.world_to_screen(wp_x, wp_y)
                points.append((wp_sx, wp_sy))
            points.append((sx2, sy2))
            
            # 대시 라인으로 그리기
            for i in range(len(points) - 1):
                self._draw_dashed_line(points[i], points[i+1], (100, 255, 100), 3)
            
            # waypoint 위치에 큰 원 그리기 (편집 가능 표시)
            for i, (wp_x, wp_y) in enumerate(self.drawer.temp_waypoints):
                wp_sx, wp_sy = self.drawer.world_to_screen(wp_x, wp_y)
                
                # 드래그 중인 waypoint는 다른 색상으로 표시
                if self.drawer.dragging_waypoint and self.drawer.dragging_waypoint_index == i:
                    # 드래그 중인 waypoint - 더 큰 크기와 빨간색
                    pygame.draw.circle(self.screen, (255, 255, 255), (int(wp_sx), int(wp_sy)), 12)
                    pygame.draw.circle(self.screen, (255, 100, 100), (int(wp_sx), int(wp_sy)), 10)
                    pygame.draw.circle(self.screen, (255, 200, 200), (int(wp_sx), int(wp_sy)), 6)
                else:
                    # 일반 waypoint - 초록색
                    pygame.draw.circle(self.screen, (255, 255, 255), (int(wp_sx), int(wp_sy)), 8)
                    pygame.draw.circle(self.screen, (100, 255, 100), (int(wp_sx), int(wp_sy)), 6)
            
            # 마우스 위치에 미리보기 waypoint
            mx, my = pygame.mouse.get_pos()
            pygame.draw.circle(self.screen, (255, 255, 255, 128), (mx, my), 6)
            pygame.draw.circle(self.screen, (100, 255, 100, 128), (mx, my), 4)
    
    def _draw_dashed_line(self, start, end, color, width):
        """대시 라인 그리기 함수"""
        dash_length = 10
        space_length = 5
        total_length = math.hypot(end[0]-start[0], end[1]-start[1])
        if total_length < 1:
            return
        angle = math.atan2(end[1]-start[1], end[0]-start[0])
        dash_count = int(total_length / (dash_length + space_length))
        for i in range(dash_count + 1):
            start_dist = i * (dash_length + space_length)
            end_dist = min(start_dist + dash_length, total_length)
            if start_dist >= total_length:
                break
            dash_start_x = start[0] + math.cos(angle) * start_dist
            dash_start_y = start[1] + math.sin(angle) * start_dist
            dash_end_x = start[0] + math.cos(angle) * end_dist
            dash_end_y = start[1] + math.sin(angle) * end_dist
            pygame.draw.line(self.screen, color,
                           (dash_start_x, dash_start_y),
                           (dash_end_x, dash_end_y), width)
    
    def _catmull_rom_spline(self, points, segments=20):
        """점들을 부드러운 곡선으로 연결하는 Catmull-Rom spline"""
        if len(points) < 2:
            return points
        if len(points) == 2:
            return points
        
        # 추가 제어점 생성 (첫 번째와 마지막 점 연장)
        extended_points = []
        
        # 첫 번째 점의 확장 (첫 번째와 두 번째 점의 방향으로)
        if len(points) >= 2:
            dx = points[0][0] - points[1][0]
            dy = points[0][1] - points[1][1]
            extended_points.append((points[0][0] + dx, points[0][1] + dy))
        
        extended_points.extend(points)
        
        # 마지막 점의 확장
        if len(points) >= 2:
            dx = points[-1][0] - points[-2][0]
            dy = points[-1][1] - points[-2][1]
            extended_points.append((points[-1][0] + dx, points[-1][1] + dy))
        
        smooth_points = []
        
        # 각 구간에 대해 곡선 생성
        for i in range(1, len(extended_points) - 2):
            p0 = extended_points[i - 1]
            p1 = extended_points[i]
            p2 = extended_points[i + 1]
            p3 = extended_points[i + 2]
            
            for j in range(segments):
                t = j / segments
                
                # Catmull-Rom 공식
                x = 0.5 * (
                    (2 * p1[0]) +
                    (-p0[0] + p2[0]) * t +
                    (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t * t +
                    (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t * t * t
                )
                
                y = 0.5 * (
                    (2 * p1[1]) +
                    (-p0[1] + p2[1]) * t +
                    (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t * t +
                    (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t * t * t
                )
                
                smooth_points.append((x, y))
        
        # 마지막 점 추가
        if extended_points:
            smooth_points.append(extended_points[-2])  # 실제 마지막 점
        
        return smooth_points
    
    def _point_to_line_distance(self, px, py, x1, y1, x2, y2):
        """점 (px, py)에서 선분 (x1,y1)-(x2,y2)까지의 최단거리"""
        # 선분의 길이의 제곱
        line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        
        if line_length_sq == 0:
            # 선분이 점인 경우
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        
        # 선분 위의 가장 가까운 점 계산
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / line_length_sq))
        
        # 가장 가까운 점의 좌표
        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)
        
        # 거리 계산
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
    
    def _draw_smooth_line(self, points, color, width):
        """점들을 부드러운 곡선으로 연결하여 그리기"""
        if len(points) < 2:
            return
        
        if len(points) == 2:
            # 점이 2개이면 직선
            pygame.draw.line(self.screen, color, points[0], points[1], width)
            return
        
        # 3개 이상이면 부드러운 곡선
        smooth_points = self._catmull_rom_spline(points, segments=15)
        
        # 곡선을 여러 개의 짧은 선분으로 그리기
        for i in range(len(smooth_points) - 1):
            pygame.draw.line(self.screen, color, smooth_points[i], smooth_points[i + 1], width)

    def _draw_power_lines(self):
        """송전선 그리기"""
        for pl in self.simulator.city.lines:
            if pl.removed:
                continue
            if self.simulator.city.buildings[pl.u].removed or self.simulator.city.buildings[pl.v].removed:
                continue
                
            # 시작점과 끝점 건물 좌표 가져오기
            x1 = self.simulator.city.buildings[pl.u].x
            y1 = self.simulator.city.buildings[pl.u].y
            x2 = self.simulator.city.buildings[pl.v].x
            y2 = self.simulator.city.buildings[pl.v].y
            sx1, sy1 = self.drawer.world_to_screen(x1, y1)
            sx2, sy2 = self.drawer.world_to_screen(x2, y2)
            
            # 사용률에 따른 색상 계산
            usage = 0
            if pl.capacity > 1e-9:
                usage = abs(pl.flow) / pl.capacity
                if usage > 1:
                    usage = 1
            r = int(200 * usage)
            g = int(200 * (1 - usage))
            color = (r, g, 0)
            thick = max(3, int(3 + 7 * usage))
            
            # waypoint 선택 모드에서 호버 효과
            if self.drawer.add_mode == "select_line_for_waypoint":
                mx, my = pygame.mouse.get_pos()
                # 선에서 마우스까지의 거리 계산
                line_dist = self._point_to_line_distance(mx, my, sx1, sy1, sx2, sy2)
                if line_dist < 15:  # 15픽셀 내에 있으면 하이라이트
                    color = (100, 255, 100)  # 초록색으로 하이라이트
                    thick = max(thick + 2, 8)  # 더 두껍게
            
            # 파티클 생성
            if abs(pl.flow) > 0.1:  # 의미있는 전력 흐름이 있을 때만
                b_start = self.simulator.city.buildings[pl.u]
                b_end = self.simulator.city.buildings[pl.v]
                self.drawer.particles.spawn_particles_for_line(pl, b_start, b_end, self.drawer.clock.get_time())
            
            # waypoint가 있으면 waypoint를 거쳐서 그리기
            if hasattr(pl, 'waypoints') and pl.waypoints:
                # 모든 점들을 순서대로 연결
                points = [(sx1, sy1)]
                for wp_x, wp_y in pl.waypoints:
                    wp_sx, wp_sy = self.drawer.world_to_screen(wp_x, wp_y)
                    points.append((wp_sx, wp_sy))
                points.append((sx2, sy2))
                
                # 글로우 효과 (부드러운 곡선으로)
                if usage > 0.2:
                    glow_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    glow_col = (r, g, 0, 80)
                    if len(points) > 2:
                        # 부드러운 곡선으로 글로우 효과
                        smooth_points = self._catmull_rom_spline(points, segments=10)
                        for i in range(len(smooth_points) - 1):
                            pygame.draw.line(glow_surf, glow_col, smooth_points[i], smooth_points[i+1], thick + 8)
                    else:
                        # waypoint가 없거나 적으면 직선
                        for i in range(len(points) - 1):
                            pygame.draw.line(glow_surf, glow_col, points[i], points[i+1], thick + 8)
                    self.screen.blit(glow_surf, (0, 0))
                
                # 메인 라인 그리기 (부드러운 곡선으로)
                if len(points) > 2:
                    # 3개 이상의 점이 있으면 부드러운 곡선
                    self._draw_smooth_line(points, color, thick)
                else:
                    # waypoint가 없거나 적으면 직선
                    for i in range(len(points) - 1):
                        pygame.draw.line(self.screen, color, points[i], points[i+1], thick)
                
                # waypoint 위치에 작은 원 그리기 (편집 가능한 지점 표시)
                for wp_x, wp_y in pl.waypoints:
                    wp_sx, wp_sy = self.drawer.world_to_screen(wp_x, wp_y)
                    pygame.draw.circle(self.screen, (255, 255, 255), (int(wp_sx), int(wp_sy)), 4)
                    pygame.draw.circle(self.screen, color, (int(wp_sx), int(wp_sy)), 3)
                
                # 화살표는 첫 번째 구간에만 그리기
                if abs(pl.flow) > 0.1 and len(points) >= 2:
                    if len(points) > 2:
                        # 곡선의 경우 시작 방향 계산
                        smooth_points = self._catmull_rom_spline(points, segments=10)
                        if len(smooth_points) >= 2:
                            if pl.flow > 0:
                                draw_arrow(self.screen, smooth_points[0][0], smooth_points[0][1], 
                                          smooth_points[1][0], smooth_points[1][1], color, thick)
                            else:
                                draw_arrow(self.screen, smooth_points[-1][0], smooth_points[-1][1], 
                                          smooth_points[-2][0], smooth_points[-2][1], color, thick)
                    else:
                        # 직선의 경우
                        if pl.flow > 0:
                            draw_arrow(self.screen, points[0][0], points[0][1], points[1][0], points[1][1], color, thick)
                        else:
                            draw_arrow(self.screen, points[-1][0], points[-1][1], points[-2][0], points[-2][1], color, thick)
            else:
                # waypoint가 없으면 기존 방식대로 직선 그리기
                # 글로우 효과
                if usage > 0.2:
                    glow_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    glow_col = (r, g, 0, 80)
                    pygame.draw.line(glow_surf, glow_col, (sx1, sy1), (sx2, sy2), thick + 8)
                    self.screen.blit(glow_surf, (0, 0))
                
                # 메인 라인
                pygame.draw.line(self.screen, color, (sx1, sy1), (sx2, sy2), thick)
                if abs(pl.flow) > 0.1:
                    if pl.flow > 0:
                        draw_arrow(self.screen, sx1, sy1, sx2, sy2, color, thick)
                    else:
                        draw_arrow(self.screen, sx2, sy2, sx1, sy1, color, thick)
            
            # 마우스가 송전선 근처에 있을 때만 정보 박스 그리기
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # 송전선의 중앙점 계산
            mid_x = (sx1 + sx2) / 2
            mid_y = (sy1 + sy2) / 2
            # 마우스와 중앙점 사이의 거리 계산
            dist_to_mouse = ((mouse_x - mid_x) ** 2 + (mouse_y - mid_y) ** 2) ** 0.5
            
            # 마우스가 송전선 근처(50픽셀 이내)에 있을 때만 정보 표시
            if dist_to_mouse < 50:
                self._draw_line_info(pl, sx1, sy1, sx2, sy2, usage)
    
    def _draw_line_info(self, pl, sx1, sy1, sx2, sy2, usage):
        """송전선 중앙에 정보 박스 그리기"""
        mid_x = (sx1 + sx2) / 2
        mid_y = (sy1 + sy2) / 2
        info_color = (0, 200, 0) if usage < 0.5 else (200, 200, 0) if usage < 0.8 else (200, 0, 0)
        usage_percent = usage * 100
        flow_text = f"{abs(pl.flow):.1f}/{pl.capacity:.1f} MW"
        usage_text = f"{usage_percent:.0f}%"
        voltage_text = "345kV" if pl.capacity > 500 else "154kV" if pl.capacity > 200 else "22.9kV"
        if usage > 0.8:
            warning = "⚠" if usage > 0.95 else "!"
            flow_text = warning + " " + flow_text
        
        # 텍스트 렌더링 함수
        def render_text_with_shadow(text, color):
            shadow_surf = self.small_font.render(text, True, (0, 0, 0))
            text_surf = self.small_font.render(text, True, color)
            combined = pygame.Surface((text_surf.get_width() + 2, text_surf.get_height() + 2), pygame.SRCALPHA)
            combined.blit(shadow_surf, (2, 2))
            combined.blit(text_surf, (0, 0))
            return combined
        
        flow_surf = render_text_with_shadow(flow_text, info_color)
        usage_surf = render_text_with_shadow(usage_text, info_color)
        voltage_surf = render_text_with_shadow(voltage_text, (150, 150, 255))
        
        # 박스 크기 및 위치 계산
        padding = 4
        margin = 2
        box_width = max(flow_surf.get_width(), usage_surf.get_width(), voltage_surf.get_width()) + padding * 2
        box_height = flow_surf.get_height() + usage_surf.get_height() + voltage_surf.get_height() + padding * 2 + margin * 2
        box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        box.fill((0, 0, 0, 160))
        
        # 텍스트 배치
        flow_x = (box_width - flow_surf.get_width()) / 2
        usage_x = (box_width - usage_surf.get_width()) / 2
        voltage_x = (box_width - voltage_surf.get_width()) / 2
        box.blit(flow_surf, (flow_x, padding))
        box.blit(usage_surf, (usage_x, padding + flow_surf.get_height() + margin))
        box.blit(voltage_surf, (voltage_x, padding + flow_surf.get_height() + usage_surf.get_height() + margin * 2))
        
        # 박스 위치 조정 (화면 경계 넘지 않도록)
        box_x = mid_x - box_width / 2
        box_y = mid_y - box_height / 2
        if box_x < 0: box_x = 0
        if box_y < 0: box_y = 0
        if box_x + box_width > self.width: box_x = self.width - box_width
        if box_y + box_height > self.height: box_y = self.height - box_height
        
        # 화면에 그리기
        self.screen.blit(box, (box_x, box_y))

    def draw_building(self, b):
        """건물 그리기"""
        sx, sy = self.drawer.world_to_screen(b.x, b.y)
        base_r = 25
        size_factor = min(2.0, max(0.8, 1.0 + abs(b.current_supply) / 10.0))
        r = base_r * size_factor
        
        # 송전선 추가/삭제 모드에서 glow 효과
        self._draw_building_mode_effects(b, sx, sy, r)
        
        # 그림자 그리기
        shadow_col = (0, 0, 0, 60)
        sh_off = 4
        shadow_surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surf, shadow_col, (r + 4, r + 4), r + 3)
        self.screen.blit(shadow_surf, (sx - (r + 4), sy - (r + 4)))
        
        # 건물 색상 결정
        col, border_col = self._get_building_colors(b)
        
        # 발전소 타입별로 다른 모양 그리기
        if hasattr(b, 'power_plant_type') and b.power_plant_type:
            self._draw_power_plant_by_type(b, sx, sy, r, col, border_col)
        elif b.base_supply > 0:
            # 기본 발전소 - 번개 모양
            self._draw_generator_shape(b, sx, sy, r, col, border_col)
        else:
            # 소비 건물 - 집 모양
            self._draw_consumer_shape(b, sx, sy, r, col, border_col)
        
        # 정보박스(건물 이름/수요/공급 등) - 호버 중일 때만 표시
        # (툴팁으로 표시되므로 여기서는 표시하지 않음)
        # self._draw_building_info(b, sx, sy, r)
    
    def _draw_building_mode_effects(self, b, sx, sy, r):
        """모드에 따른 건물 효과 그리기"""
        if self.drawer.add_mode == "add_line":
            glow_size = r + 8
            glow_color = (255, 255, 100, 100)
            if self.drawer.temp_line_start is None:
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                self.screen.blit(glow_surf, (sx - glow_size, sy - glow_size))
            elif b != self.drawer.temp_line_start:
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
                self.screen.blit(glow_surf, (sx - glow_size, sy - glow_size))
        elif self.drawer.add_mode == "delete":
            glow_size = r + 8
            glow_color = (255, 100, 100, 100)
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, glow_color, (glow_size, glow_size), glow_size)
            self.screen.blit(glow_surf, (sx - glow_size, sy - glow_size))
    
    def _get_building_colors(self, b):
        """건물 상태에 따른 색상 결정"""
        if b.base_supply > 0:
            # 발전소 - 타입별 색상
            if hasattr(b, 'power_plant_type') and b.power_plant_type:
                if b.power_plant_type == "nuclear":
                    col = (255, 150, 150)  # 빨간색 계열 (원자력)
                    border_col = (255, 100, 100)
                elif b.power_plant_type == "thermal":
                    col = (150, 120, 100)  # 갈색 계열 (화력)
                    border_col = (120, 80, 60)
                elif b.power_plant_type == "wind":
                    col = (150, 200, 255)  # 하늘색 계열 (풍력)
                    border_col = (100, 150, 255)
                elif b.power_plant_type == "solar":
                    col = (255, 220, 100)  # 노란색 계열 (태양광)
                    border_col = (255, 200, 50)
                elif b.power_plant_type == "hydro":
                    col = (100, 150, 255)  # 파란색 계열 (수력)
                    border_col = (50, 100, 200)
                elif b.power_plant_type == "hydrogen":
                    col = (200, 150, 255)  # 보라색 계열 (수소)
                    border_col = (150, 100, 255)
                else:
                    col = (100, 150, 255)  # 기본 발전소
                    border_col = (100, 200, 255)
            else:
                col = (100, 150, 255)  # 기본 발전소
                border_col = (100, 200, 255)
        elif b.base_supply < 0:
            # 수요 건물
            if b.blackout: # b.blackout은 현재 수요 기준으로 check_blackouts에서 이미 계산됨
                # 정전된 건물은 깜빡임
                if (pygame.time.get_ticks() // 500) % 2:
                    col = (255, 100, 100) # 밝은 빨강
                    border_col = (255, 150, 150)
                else:
                    col = (200, 50, 50) # 어두운 빨강
                    border_col = (255, 100, 100)
            else:
                # 정상 작동 수요 건물 (b.shortage가 0에 가까움)
                col = (100, 200, 100) # 녹색 계열
                border_col = (150, 255, 150)
                # 만약 b.shortage 값에 따라 미세한 색상 변화를 주고 싶다면 추가 가능
                # 예를 들어, b.shortage가 현재수요 대비 특정 % 이상이면 노란색 계열 등으로...
                # current_demand = -b.current_supply if b.current_supply < 0 else 0
                # if current_demand > 1e-9 and hasattr(b, 'shortage') and b.shortage > 0:
                #    shortage_ratio_for_color = b.shortage / current_demand
                #    if shortage_ratio_for_color > 0.05: # 예: 5% 이상 부족하면 노란색
                #        col = (200, 200, 100)
                #        border_col = (255, 255, 150)

        elif b.solar_capacity > 0: # 중립적이면서 태양광이 있는 경우 (프로슈머 등)
            if b.is_prosumer:
                col = (150, 200, 50) # 프로슈머 색상
                border_col = (200, 255, 100)
            else:
                col = (200, 200, 50) # 일반 태양광 건물 색상
                border_col = (255, 255, 100)
        else:
            # 중립 건물 (수요도 공급도 아닌 경우, 예: base_supply = 0이고 태양광도 없는 경우)
            col = (150, 150, 150)
            border_col = (200, 200, 200)
        
        return col, border_col
    
    def _draw_generator_shape(self, b, sx, sy, r, col, border_col):
        """발전소 모양 그리기"""
        # 발전소 타입에 따라 다른 모양 그리기
        if hasattr(b, 'power_plant_type'):
            if b.power_plant_type == "wind":
                # 풍력발전소 - 풍차 모양
                self._draw_wind_turbine(sx, sy, r, col, border_col)
            elif b.power_plant_type == "solar":
                # 태양광발전소 - 태양 패널 모양
                self._draw_solar_panel(sx, sy, r, col, border_col)
            elif b.power_plant_type == "hydro":
                # 수력발전소 - 물방울 모양
                self._draw_hydro_plant(sx, sy, r, col, border_col)
            elif b.power_plant_type == "hydrogen":
                # 수소저장소 - H2 탱크 모양
                self._draw_hydrogen_storage(sx, sy, r, col, border_col)
            else:
                # 기본 발전소 - 번개 모양
                self._draw_lightning_shape(sx, sy, r, col, border_col)
        else:
            # 기본 발전소 - 번개 모양
            self._draw_lightning_shape(sx, sy, r, col, border_col)

    def _draw_power_plant_by_type(self, b, sx, sy, r, col, border_col):
        """발전소 타입별 아이콘 그리기"""
        if b.power_plant_type == "wind":
            # 풍력발전소 - 풍차 모양
            # 중심 원
            pygame.draw.circle(self.screen, col, (sx, sy), r)
            pygame.draw.circle(self.screen, border_col, (sx, sy), r, 3)
            
            # 풍차 날개 (3개)
            for i in range(3):
                angle = i * 120 + self.drawer.frame_count * 2  # 회전 애니메이션
                rad = math.radians(angle)
                x1 = sx + math.cos(rad) * r * 0.8
                y1 = sy + math.sin(rad) * r * 0.8
                x2 = sx + math.cos(rad + math.radians(15)) * r * 0.6
                y2 = sy + math.sin(rad + math.radians(15)) * r * 0.6
                x3 = sx + math.cos(rad - math.radians(15)) * r * 0.6
                y3 = sy + math.sin(rad - math.radians(15)) * r * 0.6
                
                pygame.draw.polygon(self.screen, (255, 255, 255), 
                                   [(sx, sy), (x1, y1), (x2, y2)])
                pygame.draw.polygon(self.screen, (255, 255, 255), 
                                   [(sx, sy), (x1, y1), (x3, y3)])
            
            # 중심점
            pygame.draw.circle(self.screen, (50, 50, 50), (sx, sy), r // 4)
            
        elif b.power_plant_type == "solar":
            # 태양광발전소 - 태양 패널 모양
            pygame.draw.circle(self.screen, col, (sx, sy), r)
            pygame.draw.circle(self.screen, border_col, (sx, sy), r, 3)
            
            # 태양광 패널 격자
            panel_size = r * 0.6
            pygame.draw.rect(self.screen, (20, 50, 100), 
                           (sx - panel_size, sy - panel_size, panel_size * 2, panel_size * 2))
            
            # 패널 격자선
            for i in range(3):
                offset = -panel_size + (i + 1) * panel_size * 2 / 3
                pygame.draw.line(self.screen, (150, 150, 200), 
                               (sx + offset, sy - panel_size), 
                               (sx + offset, sy + panel_size), 2)
                pygame.draw.line(self.screen, (150, 150, 200), 
                               (sx - panel_size, sy + offset), 
                               (sx + panel_size, sy + offset), 2)
            
            # 태양 광선 효과
            if b.current_supply > 0:
                for i in range(8):
                    angle = i * 45
                    rad = math.radians(angle)
                    x1 = sx + math.cos(rad) * (r + 5)
                    y1 = sy + math.sin(rad) * (r + 5)
                    x2 = sx + math.cos(rad) * (r + 15)
                    y2 = sy + math.sin(rad) * (r + 15)
                    pygame.draw.line(self.screen, (255, 220, 100), (x1, y1), (x2, y2), 2)
                    
        elif b.power_plant_type == "hydro":
            # 수력발전소 - 물방울/댐 모양
            pygame.draw.circle(self.screen, col, (sx, sy), r)
            pygame.draw.circle(self.screen, border_col, (sx, sy), r, 3)
            
            # 물방울 모양
            points = [
                (sx, sy - r * 0.7),  # 위
                (sx - r * 0.5, sy),  # 왼쪽
                (sx, sy + r * 0.4),  # 아래
                (sx + r * 0.5, sy),  # 오른쪽
            ]
            pygame.draw.polygon(self.screen, (100, 150, 255), points)
            
            # 물결 효과
            wave_offset = (self.drawer.frame_count % 60) / 60 * math.pi * 2
            for i in range(3):
                y = sy + r * 0.2 - i * 5
                x1 = sx - r * 0.4
                x2 = sx + r * 0.4
                points = []
                for x in range(int(x1), int(x2), 3):
                    wave_y = y + math.sin((x - x1) / 10 + wave_offset) * 3
                    points.append((x, wave_y))
                if len(points) > 1:
                    pygame.draw.lines(self.screen, (255, 255, 255), False, points, 2)
                    
        elif b.power_plant_type == "hydrogen":
            # 수소 저장소 - H2 심볼
            pygame.draw.circle(self.screen, col, (sx, sy), r)
            pygame.draw.circle(self.screen, border_col, (sx, sy), r, 3)
            
            # H2 텍스트
            font = pygame.font.Font(None, int(r * 0.8))
            text = font.render("H₂", True, (255, 255, 255))
            text_rect = text.get_rect(center=(sx, sy))
            self.screen.blit(text, text_rect)
            
            # 저장량 표시 (원형 게이지)
            if b.hydrogen_storage > 0:
                percentage = b.hydrogen_level / b.hydrogen_storage
                # 배경 원
                pygame.draw.circle(self.screen, (50, 50, 50), (sx, sy), r + 5, 3)
                # 진행도 아크
                if percentage > 0:
                    start_angle = -math.pi / 2
                    end_angle = start_angle + 2 * math.pi * percentage
                    points = [(sx, sy)]
                    for angle in range(int(math.degrees(start_angle)), 
                                     int(math.degrees(end_angle)), 5):
                        rad = math.radians(angle)
                        x = sx + math.cos(rad) * (r + 5)
                        y = sy + math.sin(rad) * (r + 5)
                        points.append((x, y))
                    if len(points) > 2:
                        pygame.draw.lines(self.screen, (100, 200, 255), False, points[1:], 3)
                        
        elif b.power_plant_type == "nuclear":
            # 원자력발전소 - 원자력 기호와 냉각탑
            pygame.draw.circle(self.screen, col, (sx, sy), r)
            pygame.draw.circle(self.screen, border_col, (sx, sy), r, 3)
            
            # 원자력 기호 (삼원환)
            center_r = r * 0.3
            for i in range(3):
                angle = i * 120
                rad = math.radians(angle)
                circle_x = sx + math.cos(rad) * center_r
                circle_y = sy + math.sin(rad) * center_r
                pygame.draw.circle(self.screen, (255, 255, 100), 
                                 (int(circle_x), int(circle_y)), int(r * 0.15))
                pygame.draw.circle(self.screen, (200, 200, 0), 
                                 (int(circle_x), int(circle_y)), int(r * 0.15), 2)
            
            # 중심점
            pygame.draw.circle(self.screen, (255, 100, 100), (sx, sy), int(r * 0.1))
            
            # 냉각탑 증기 효과 (발전 중일 때)
            if b.current_supply > 0:
                for i in range(4):
                    steam_x = sx - r * 0.4 + i * r * 0.2
                    steam_y = sy - r * 1.2
                    steam_size = 3 + (self.drawer.frame_count + i * 10) % 20
                    pygame.draw.circle(self.screen, (220, 220, 255, 100), 
                                     (int(steam_x), int(steam_y)), steam_size)
        
        elif b.power_plant_type == "thermal":
            # 화력발전소 - 굴뚝과 연기
            pygame.draw.circle(self.screen, col, (sx, sy), r)
            pygame.draw.circle(self.screen, border_col, (sx, sy), r, 3)
            
            # 굴뚝들
            chimney_width = r * 0.2
            for i in range(2):
                chimney_x = sx - r * 0.3 + i * r * 0.6
                chimney_rect = pygame.Rect(chimney_x - chimney_width//2, sy - r * 1.5, 
                                         chimney_width, r * 1.0)
                pygame.draw.rect(self.screen, (80, 80, 80), chimney_rect)
                pygame.draw.rect(self.screen, (60, 60, 60), chimney_rect, 2)
            
            # 연기 효과 (발전 중일 때)
            if b.current_supply > 0:
                for i in range(2):
                    for j in range(3):
                        smoke_x = sx - r * 0.3 + i * r * 0.6
                        smoke_y = sy - r * 1.5 - j * 10
                        smoke_offset = (self.drawer.frame_count + i * 20 + j * 5) % 40
                        smoke_size = 5 + smoke_offset // 10
                        smoke_alpha = 150 - j * 30
                        pygame.draw.circle(self.screen, (100, 100, 100, max(0, smoke_alpha)), 
                                         (int(smoke_x + smoke_offset * 0.2), int(smoke_y)), smoke_size)
            
            # 석탄 더미 표현
            coal_rect = pygame.Rect(sx - r * 0.4, sy + r * 0.2, r * 0.8, r * 0.3)
            pygame.draw.rect(self.screen, (40, 40, 40), coal_rect)
            pygame.draw.rect(self.screen, (20, 20, 20), coal_rect, 2)
                        
        else:
            # 기본 발전소
            self._draw_generator_shape(b, sx, sy, r, col, border_col)
    
    def _draw_lightning_shape(self, sx, sy, r, col, border_col):
        """번개 모양 그리기"""
        points = [
            (sx - r * 0.2, sy - r * 0.6),
            (sx + r * 0.1, sy - r * 0.1),
            (sx - r * 0.1, sy - r * 0.1),
            (sx + r * 0.2, sy + r * 0.6),
            (sx - r * 0.1, sy + r * 0.2),
            (sx + r * 0.1, sy + r * 0.2)
        ]
        pygame.draw.polygon(self.screen, col, points)
        pygame.draw.polygon(self.screen, border_col, points, 3)
    
    def _draw_wind_turbine(self, sx, sy, r, col, border_col):
        """풍력발전기 모양 그리기"""
        # 기둥
        pole_width = r * 0.2
        pole_height = r * 1.5
        pygame.draw.rect(self.screen, col, 
                        (sx - pole_width/2, sy - pole_height/2, pole_width, pole_height))
        # 풍차 날개 3개
        blade_length = r * 0.8
        for angle in [0, 120, 240]:
            end_x = sx + blade_length * math.cos(math.radians(angle + pygame.time.get_ticks()/10))
            end_y = sy - pole_height/2 + blade_length * math.sin(math.radians(angle + pygame.time.get_ticks()/10))
            pygame.draw.line(self.screen, border_col, (sx, sy - pole_height/2), (end_x, end_y), 3)
        # 중앙 허브
        pygame.draw.circle(self.screen, col, (int(sx), int(sy - pole_height/2)), int(r * 0.15))
    
    def _draw_solar_panel(self, sx, sy, r, col, border_col):
        """태양광 패널 모양 그리기"""
        panel_width = r * 1.4
        panel_height = r * 0.8
        # 패널 본체
        panel_rect = pygame.Rect(sx - panel_width/2, sy - panel_height/2, panel_width, panel_height)
        pygame.draw.rect(self.screen, (50, 50, 150), panel_rect)
        pygame.draw.rect(self.screen, border_col, panel_rect, 2)
        # 그리드 라인
        for i in range(1, 3):
            y_pos = sy - panel_height/2 + (panel_height/3) * i
            pygame.draw.line(self.screen, (100, 100, 200), 
                           (sx - panel_width/2, y_pos), (sx + panel_width/2, y_pos), 1)
        for i in range(1, 4):
            x_pos = sx - panel_width/2 + (panel_width/4) * i
            pygame.draw.line(self.screen, (100, 100, 200), 
                           (x_pos, sy - panel_height/2), (x_pos, sy + panel_height/2), 1)
    
    def _draw_hydro_plant(self, sx, sy, r, col, border_col):
        """수력발전소 모양 그리기"""
        # 댑 모양
        dam_width = r * 1.6
        dam_height = r * 1.2
        dam_points = [
            (sx - dam_width/2, sy + dam_height/2),
            (sx - dam_width/3, sy - dam_height/2),
            (sx + dam_width/3, sy - dam_height/2),
            (sx + dam_width/2, sy + dam_height/2)
        ]
        pygame.draw.polygon(self.screen, (100, 120, 140), dam_points)
        pygame.draw.polygon(self.screen, border_col, dam_points, 2)
        # 물방울
        for i in range(3):
            drop_x = sx - dam_width/4 + (dam_width/4) * i
            drop_y = sy + dam_height/2 + 5 + i * 3
            pygame.draw.circle(self.screen, (100, 150, 255), (int(drop_x), int(drop_y)), 3)
    
    def _draw_hydrogen_storage(self, sx, sy, r, col, border_col):
        """수소저장소 모양 그리기"""
        # 원통형 탱크
        tank_width = r * 1.2
        tank_height = r * 1.4
        tank_rect = pygame.Rect(sx - tank_width/2, sy - tank_height/2, tank_width, tank_height)
        pygame.draw.ellipse(self.screen, (150, 150, 200), tank_rect)
        pygame.draw.ellipse(self.screen, border_col, tank_rect, 2)
        # H2 텍스트
        font = pygame.font.Font(None, int(r * 0.6))
        text = font.render("H2", True, (50, 50, 100))
        text_rect = text.get_rect(center=(sx, sy))
        self.screen.blit(text, text_rect)
    
    def _draw_consumer_shape(self, b, sx, sy, r, col, border_col):
        """소비 건물 모양 그리기 (집 모양)"""
        house_w = r
        house_h = r
        roof_pts = [
            (sx, sy - r),
            (sx - house_w * 0.6, sy - r * 0.3),
            (sx + house_w * 0.6, sy - r * 0.3)
        ]
        pygame.draw.polygon(self.screen, col, roof_pts)
        pygame.draw.rect(self.screen, col, (sx - house_w * 0.5, sy - r * 0.3, house_w, house_h * 0.6))
        pygame.draw.polygon(self.screen, border_col, roof_pts, 3)
        pygame.draw.rect(self.screen, border_col, (sx - house_w * 0.5, sy - r * 0.3, house_w, house_h * 0.6), 3)
        
        # 태양광 패널 그리기
        if b.solar_capacity > 0:
            panel_h = r * 0.15
            panel_y = sy - r + panel_h
            pygame.draw.rect(self.screen, (0, 0, 0), (sx - house_w * 0.5, panel_y, house_w, panel_h))
            for i in range(3):
                x = sx - house_w * 0.4 + i * house_w * 0.3
                pygame.draw.rect(self.screen, (0, 150, 255), (x, panel_y, house_w * 0.25, panel_h))
    
    def _draw_building_info(self, b, sx, sy, r):
        """건물 정보 박스 그리기 (수정 최종안)"""
        type_txt = f"{b.get_type_str()}{b.idx}"
        status_lines = []

        # 소비자 정보 처리 (b.base_supply < 0)
        if b.base_supply < 0:
            base_demand = abs(b.base_supply) # 초기 설정된 기본 수요량
            current_demand = -b.current_supply if b.current_supply < 0 else 0 # 현재 실제 수요량

            status_lines.append(f"기본수요: {base_demand:.1f} MW") # "평균수요" -> "기본수요"로 레이블 변경
            status_lines.append(f"현재수요: {current_demand:.1f} MW") # 실시간 현재 수요 표시

            # 태양광 설비 정보 (있으면 표시)
            if b.solar_capacity > 0:
                status_lines.append(f"태양광설비: {b.solar_capacity:.1f}")

            # 부족 정보: 오직 b.shortage 값만 사용!
            if hasattr(b, 'shortage'):
                # 부족 라인 추가 (0.0도 표시되도록)
                status_lines.append(f"부족: {b.shortage:.1f}")

                # 부족률은 shortage가 0보다 클 때만 의미있게 표시
                # 부족률 계산 시 기준은 '현재수요'가 되어야 함
                if b.shortage > 1e-9 and current_demand > 1e-9:
                    shortage_ratio = (b.shortage / current_demand) * 100
                    status_lines.append(f"부족률: {shortage_ratio:.1f}%")
                elif current_demand <= 1e-9: # 현재 수요가 0이면 부족률 계산 불가
                    status_lines.append(f"부족률: -")
                # else: shortage가 0이면 부족률 라인 불필요 (이미 부족: 0.0 표시됨)
            else:
                status_lines.append(f"부족: N/A") # shortage 속성이 없는 경우

        # 생산자 정보 처리 (b.base_supply > 0)
        elif b.base_supply > 0:
            status_lines.append(f"설비용량: {b.base_supply:.1f} MW")
            if hasattr(b, 'current_supply') and abs(b.current_supply - b.base_supply) > 1e-9 :
                status_lines.append(f"현재출력: {b.current_supply:.1f} MW")

            # 송전량 정보: 오직 b.transmitted_power 값만 사용!
            if hasattr(b, 'transmitted_power'):
                 status_lines.append(f"송전량: {b.transmitted_power:.1f} MW")
                 if b.base_supply > 0:
                     utilization = (b.transmitted_power / b.base_supply) * 100
                     status_lines.append(f"이용률: {utilization:.1f}%")
            else:
                 status_lines.append(f"송전량: N/A")

        # 중립 건물 등 나머지 경우 처리
        else: # base_supply == 0
            status_lines.append(f"타입: {b.get_type_str()}")
            if b.solar_capacity > 0:
                status_lines.append(f"태양광: {b.solar_capacity:.1f} MW")
            if hasattr(b, 'current_supply') and abs(b.current_supply) > 1e-9:
                 status_lines.append(f"현재출력: {b.current_supply:.1f} MW")
            if hasattr(b, 'transmitted_power'):
                 # 중립 건물 등도 송전 가능성이 있으므로 표시
                 status_lines.append(f"송전량: {b.transmitted_power:.1f} MW")

        # 배터리 정보
        if hasattr(b, 'battery_capacity') and b.battery_capacity > 0:
            charge_percent = 0
            if b.battery_capacity > 1e-9:
                charge_percent = (b.battery_charge / b.battery_capacity) * 100
            status_lines.append(f"배터리: {b.battery_charge:.1f}/{b.battery_capacity:.1f} ({charge_percent:.0f}%)")

        # 정전 정보
        if b.blackout:
            status_lines.append("정전!")

        # 텍스트 렌더링 함수
        def render_text_with_outline(text, font, color):
            shadow_surfaces = []
            outline_color = (0, 0, 0, 220)
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                s = font.render(text, True, outline_color)
                shadow_surfaces.append((s, (dx, dy)))
            text_surface = font.render(text, True, color)
            final_surface = pygame.Surface((text_surface.get_width() + 4, text_surface.get_height() + 4), pygame.SRCALPHA)
            for surf, (dx, dy) in shadow_surfaces:
                final_surface.blit(surf, (dx + 2, dy + 2))
            final_surface.blit(text_surface, (2, 2))
            return final_surface

        # 텍스트 서피스 생성
        col, _ = self._get_building_colors(b)
        name_surf = render_text_with_outline(type_txt, self.small_font, col)
        status_surfs = [render_text_with_outline(line, self.small_font, col) for line in status_lines]

        # 박스 크기 및 위치 계산
        box_width = max([name_surf.get_width()] + [s.get_width() for s in status_surfs] if status_surfs else [name_surf.get_width()]) + 16
        current_font_height = self.small_font.get_height()
        line_spacing = 4
        box_height = name_surf.get_height() + 8
        if status_surfs:
            box_height += (len(status_surfs) * current_font_height) + ((len(status_surfs) -1) * line_spacing) + 4

        # 박스 위치 조정
        box_x = sx + r + 8
        box_y = sy - box_height // 2
        if box_x + box_width > self.width:
            box_x = sx - box_width - r - 8
        if box_y + box_height > self.height:
            box_y = self.height - box_height - 4
        if box_y < 4:
            box_y = 4

        # 정보 박스 그리기
        info_box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        info_box.fill((0, 0, 0, 160))

        # 텍스트 배치
        y_offset = 4
        info_box.blit(name_surf, (8, y_offset))
        y_offset += name_surf.get_height() + (line_spacing if status_surfs else 0)
        for i, surf in enumerate(status_surfs):
            info_box.blit(surf, (8, y_offset))
            y_offset += current_font_height
            if i < len(status_surfs) -1:
                 y_offset += line_spacing

        # 화면에 그리기
        self.screen.blit(info_box, (box_x, box_y))

    def _draw_ui_panel(self):
        """UI 패널 그리기"""
        panel_surf = pygame.Surface((self.drawer.ui_rect.width, self.drawer.ui_rect.height))
        color_top = (170, 170, 210)
        color_bottom = (130, 130, 180)
        
        # 그라데이션 배경
        for y in range(self.drawer.ui_rect.height):
            alpha = y / float(self.drawer.ui_rect.height)
            rr = int(color_top[0] * (1 - alpha) + color_bottom[0] * alpha)
            gg = int(color_top[1] * (1 - alpha) + color_bottom[1] * alpha)
            bb = int(color_top[2] * (1 - alpha) + color_bottom[2] * alpha)
            pygame.draw.line(panel_surf, (rr, gg, bb), (0, y), (self.drawer.ui_rect.width, y))
        
        # 패널 그리기
        self.screen.blit(panel_surf, (self.drawer.ui_rect.x, self.drawer.ui_rect.y))
        pygame.draw.rect(self.screen, (50, 50, 50), self.drawer.ui_rect, 2, border_radius=10)
        
        # 버튼 그리기
        for b in self.drawer.buttons:
            if hasattr(b, 'draw'):  # Button 객체인 경우
                b.draw(self.screen, self.font)
            elif isinstance(b, dict):  # dict 타입 버튼인 경우
                rect = pygame.Rect(b['x'], b['y'], b['width'], b['height'])
                
                # 마우스 호버 체크
                mouse_pos = pygame.mouse.get_pos()
                if rect.collidepoint(mouse_pos):
                    color = (100, 100, 150)
                else:
                    color = (80, 80, 120)
                
                # 버튼 배경
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
                
                # 버튼 텍스트
                font = self.small_font if hasattr(self, 'small_font') else self.font
                text = font.render(b['text'], True, (255, 255, 255))
                text_rect = text.get_rect(center=rect.center)
                self.screen.blit(text, text_rect)
    
    def _draw_power_status(self):
        """전력 공급 상황 표시 (화면 하단 개선 버전)"""
        flow_val = self.simulator.calc_total_flow()
        dem = self.simulator.city.total_demand()
        
        blackout_buildings = []
        affected_demand = 0
        for b in self.simulator.city.buildings:
            if not b.removed and b.blackout:
                blackout_buildings.append(b)
                affected_demand += abs(b.base_supply)

        current_status_text = ""
        status_color = (0, 0, 0)
        icon = ""
        blink = False
        
        panel_height = 120
        panel_y_position = self.height - panel_height - 20 # 하단에서 20px 위
        panel_rect = pygame.Rect(20, panel_y_position, self.width - self.drawer.ui_rect.width - 40, panel_height)

        if blackout_buildings or flow_val + 1e-9 < dem:
            shortage = dem - flow_val if dem > 0 else 0 # 수요가 0일때 음수 부족량 방지
            shortage_percent = (shortage / dem * 100) if dem > 1e-9 else 0
            
            blackout_info = ""
            if blackout_buildings:
                blackout_info = f" | 정전: {len(blackout_buildings)}곳 (피해규모: {affected_demand:.1f})"

            if len(blackout_buildings) > 0 or shortage_percent > 50: # 50% 이상 부족 또는 정전 발생 시
                status_color = (220, 50, 50) # 진한 빨강
                icon = "⚠"
                current_status_text = f"전력 위기! 공급 {flow_val:.1f} < 수요 {dem:.1f} (부족률 {shortage_percent:.1f}%){blackout_info}"
                blink = True
                if shortage_percent > 30 or blackout_buildings: # 부가 메시지 조건은 유지
                    additional_message = "즉시 조치가 필요합니다!"
            elif shortage_percent > 20: # 20% ~ 50% 부족
                status_color = (255, 130, 0) # 주황색
                icon = "!"
                current_status_text = f"전력 부족. 공급 {flow_val:.1f} < 수요 {dem:.1f} (부족률 {shortage_percent:.1f}%){blackout_info}"
                blink = (pygame.time.get_ticks() // 700) % 2 # 약간 느린 깜빡임
            elif shortage_percent > 0: # 0% ~ 20% 부족
                status_color = (255, 200, 0) # 노란색
                icon = "!"
                current_status_text = f"경미한 전력 부족. 공급 {flow_val:.1f} < 수요 {dem:.1f} (부족률 {shortage_percent:.1f}%)"
            else: # flow_val < dem 이지만 shortage_percent가 0인 경우 (매우 작은 차이)
                status_color = (50, 180, 50) # 녹색
                icon = "✔"
                current_status_text = f"전력 안정. 공급 {flow_val:.1f} ≈ 수요 {dem:.1f}"

        else:
            status_color = (50, 180, 50) # 녹색
            icon = "✔"
            current_status_text = f"전력 공급 안정. 공급 {flow_val:.1f} / 수요 {dem:.1f}"

        # 깜빡임 효과 적용
        if blink and (pygame.time.get_ticks() // 500) % 2:
            # 깜빡일 때는 내용을 안그리거나, 투명도를 조절할 수 있음. 여기서는 그냥 건너뛰어 숨김
            return

        # 배경 패널 그리기
        bg_surface = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        bg_surface.fill((30, 30, 40, 200)) # 반투명 어두운 배경
        pygame.draw.rect(bg_surface, status_color, (0,0,panel_rect.width, 5), border_top_left_radius=10, border_top_right_radius=10) # 상단 상태 바
        self.screen.blit(bg_surface, panel_rect.topleft)
        pygame.draw.rect(self.screen, (100,100,120, 220), panel_rect, 2, border_radius=10) # 테두리
        
        # 아이콘 + 상태 텍스트
        if icon:
            icon_surf = self.big_font.render(icon, True, status_color)
            icon_rect = icon_surf.get_rect(left=panel_rect.left + 20, centery=panel_rect.centery - 15)
            self.screen.blit(icon_surf, icon_rect)
            text_start_x = icon_rect.right + 15
        else:
            text_start_x = panel_rect.left + 20

        status_surf = self.font.render(current_status_text, True, (230, 230, 240)) # 밝은 텍스트 색상
        status_rect = status_surf.get_rect(left=text_start_x, centery=panel_rect.centery - 15)
        self.screen.blit(status_surf, status_rect)
        
        # 추가 메시지 (필요시)
        if 'additional_message' in locals() and additional_message:
            add_surf = self.small_font.render(additional_message, True, (255,100,100))
            add_rect = add_surf.get_rect(left=text_start_x, centery=panel_rect.centery + 20)
            self.screen.blit(add_surf, add_rect)
            
    def _draw_mode_info(self):
        """모드 및 예산 정보 표시"""
        # 현재 모드 표시
        mode_txt = f"모드: {self.drawer.add_mode}"
        ms = self.font.render(mode_txt, True, (0, 0, 0))
        self.screen.blit(ms, (self.width - self.drawer.panel_width + 20, self.height - 120))
        
        # 예산 정보 표시 (자금 -> 예산으로 통일)
        bd_txt = f"예산: {self.simulator.budget:.1f}"
        bs = self.font.render(bd_txt, True, (0, 0, 100))
        self.screen.blit(bs, (self.width - self.drawer.panel_width + 20, self.height - 60))
    
    def _draw_time_weather(self):
        """시간 및 날씨 정보 표시"""
        # 시간, 요일, 계절 정보 가져오기
        current_time = self.simulator.simTime
        wday_kr = ["월", "화", "수", "목", "금", "토", "일"][current_time.weekday()]
        time_str = f"{current_time.year}-{current_time.month:02d}-{current_time.day:02d} {current_time.hour:02d}:{current_time.minute:02d}"
        season = self.simulator.get_current_season()
        
        # 날씨 아이콘 매핑
        icon_map = {
            "맑음": "☀",
            "흐림": "☁",
            "비": "🌧",
            "눈": "❄"
        }
        wicon = icon_map.get(self.simulator.weather_system.current_weather, "☀")
        
        # 시간 정보 표시
        kr_time = f"{time_str} ({wday_kr}) [{season}] {wicon}"
        ts = self.font.render(f"시간: {kr_time}", True, (0, 0, 0))
        shadow_ts = self.font.render(f"시간: {kr_time}", True, (255, 255, 255))
        self.screen.blit(shadow_ts, (11, 11))
        self.screen.blit(ts, (10, 10))
        
        # 날씨 정보 표시
        weather_info = (
            f"날씨: {self.simulator.weather_system.current_weather}\n"
            f"기온: {self.simulator.weather_system.current_temperature:.1f}°C\n"
            f"습도: {self.simulator.weather_system.humidity:.1f}%\n"
            f"구름: {self.simulator.weather_system.cloud_factor*100:.0f}%\n"
            f"태양광: {self.simulator.weather_system.get_potential_solar_generation_ratio()*100:.2f}%"
        )
        
        # 멀티라인 텍스트 렌더링
        y_offset = 40
        for line in weather_info.split('\n'):
            ws = self.font.render(line, True, (0, 0, 0))
            shadow_ws = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(shadow_ws, (11, y_offset + 1))
            self.screen.blit(ws, (10, y_offset))
            y_offset += 30

    def draw_help_overlay(self):
        """도움말 오버레이 표시"""
        w = self.drawer.panel_width + 100
        h = self.height // 2 + 160
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((240, 240, 255, 220))
        self.screen.blit(overlay, (10, 10))
        
        # 도움말 텍스트
        lines = [
            "[도움말 - F1]",
            "ESC: 종료",
            "R: 전체 복원",
            "",
            "마우스 왼드래그 => 건물 이동",
            "오른클릭 => 건물/송전선 컨텍스트 메뉴",
            "휠 => 줌",
            "",
            "수요(아파트)는 시간대/날씨에 따라 변동",
            "발전소(>0)는 기본 공급 유지",
            "정전은 공급 부족 시 발생",
            "",
            "시나리오 목록 => 불러오기",
            "상태 저장 => output_save.json",
            "AI 업그레이드 => 용량 or 발전량 증가"
        ]
        
        fx = 25
        fy = 25
        for i, ln in enumerate(lines):
            shadow = self.font.render(ln, True, (0, 0, 0, 120))
            text = self.font.render(ln, True, (0, 0, 0))
            self.screen.blit(shadow, (fx + 1, fy + 1 + i * 22))
            self.screen.blit(text, (fx, fy + i * 22))
    
    def draw_scenario_list(self):
        """시나리오 목록 표시"""
        w = 800
        h = 800
        left = (self.width - w) // 2
        top = 50
        panel_rect = pygame.Rect(left, top, w, h)
        shadow_rect = panel_rect.copy()
        shadow_rect.x += 5
        shadow_rect.y += 5
        
        # 배경 그리기
        pygame.draw.rect(self.screen, (180, 180, 200), shadow_rect, border_radius=10)
        pygame.draw.rect(self.screen, (240, 240, 255), panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, (50, 50, 50), panel_rect, 2, border_radius=10)
        
        # 제목 표시
        txt = self.big_font.render("시나리오 목록", True, (0, 0, 0))
        txt_rect = txt.get_rect(centerx=panel_rect.centerx, top=top + 20)
        self.screen.blit(txt, txt_rect)
        
        # 닫기 버튼 (X)
        close_btn = pygame.Rect(panel_rect.right - 40, panel_rect.top + 10, 30, 30)
        pygame.draw.rect(self.screen, (255, 100, 100), close_btn, border_radius=5)
        pygame.draw.rect(self.screen, (150, 50, 50), close_btn, 2, border_radius=5)
        close_txt = self.font.render("X", True, (255, 255, 255))
        close_txt_rect = close_txt.get_rect(center=close_btn.center)
        self.screen.blit(close_txt, close_txt_rect)
        
        # 시나리오 목록 표시 영역 (클리핑 적용)
        item_h = 80
        item_gap = 12
        item_padding_y = 15 # 항목 내부 상하단 여백
        text_gap = 6       # 이름과 설명 사이 간격
        button_margin_x = 20 # 버튼 좌우 여백
        text_margin_x = 20   # 텍스트 좌우 여백
        
        # 클리핑 영역 설정 (제목 아래부터 패널 하단까지)
        clip_rect = pygame.Rect(left + 10, top + 70, w - 20, h - 90)
        self.screen.set_clip(clip_rect)

        ycur = top + 80 - self.drawer.scenario_scroll
        # 모든 시나리오 표시
        for i, scen in enumerate(self.simulator.scenarios):
            # 목록 항목 배경 (호버 효과 추가)
            irect = pygame.Rect(left + 30, ycur, w - 60, item_h)
            
            # 마우스 호버 체크
            mx, my = pygame.mouse.get_pos()
            if irect.collidepoint(mx, my):
                # 호버 상태일 때 밝은 색상
                pygame.draw.rect(self.screen, (220, 220, 240), irect, border_radius=8)
                pygame.draw.rect(self.screen, (100, 100, 200), irect, 2, border_radius=8)
            else:
                # 일반 상태
                pygame.draw.rect(self.screen, (210, 210, 230), irect, border_radius=8)
                pygame.draw.rect(self.screen, (100, 100, 130), irect, 1, border_radius=8)

            # 시나리오 이름 (폰트 크기 조정: self.small_font 사용)
            nm_text = f"{i}) {scen['name']}"
            # 이름도 너무 길면 잘라낼 수 있지만, 폰트 크기를 줄였으므로 우선 그대로 둠
            # 필요하다면 이름에도 _truncate_text 적용 가능
            nm_s = self.small_font.render(nm_text, True, (0, 0, 0)) # self.scenario_name_font -> self.small_font
            name_render_rect = nm_s.get_rect(left=irect.x + text_margin_x, top=irect.y + item_padding_y)
            self.screen.blit(nm_s, name_render_rect)
            
            # 시나리오 설명
            desc_text = scen.get("desc", "(설명 없음)")
            # 사용 가능한 너비 계산: 항목 전체 너비 - 좌우 텍스트 여백
            available_desc_width = irect.width - (text_margin_x * 2) - 20
            
            truncated_desc = self._truncate_text(desc_text, self.small_font, available_desc_width)
            desc_s = self.small_font.render(truncated_desc, True, (70, 70, 70))
            # 이름 바로 아래에 설명 배치
            desc_render_rect = desc_s.get_rect(left=irect.x + text_margin_x, top=name_render_rect.bottom + text_gap)
            self.screen.blit(desc_s, desc_render_rect)
            
            # 클릭 가능 힌트 텍스트 (우측에 작게)
            if irect.collidepoint(mx, my):
                hint_text = "클릭하여 불러오기"
                hint_s = self.small_font.render(hint_text, True, (100, 100, 200))
                hint_rect = hint_s.get_rect(right=irect.right - text_margin_x, centery=irect.centery)
                self.screen.blit(hint_s, hint_rect)
            
            ycur += item_h + item_gap
        
        # 클리핑 해제
        self.screen.set_clip(None)
        
        # 스크롤바 표시 (시나리오가 많을 때) - 클리핑 영역 밖에 그리기
        total_height = (item_h + item_gap) * len(self.simulator.scenarios)
        visible_height = h - 100  # 상단 여백 제외
        if total_height > visible_height:
            # 스크롤바 높이 계산
            bar_height = max(30, (visible_height / total_height) * visible_height)
            # 스크롤바 위치 계산
            max_scroll = total_height - visible_height
            scroll_ratio = min(1.0, self.drawer.scenario_scroll / max_scroll) if max_scroll > 0 else 0
            bar_pos = top + 80 + scroll_ratio * (visible_height - bar_height)
            
            # 스크롤바 그리기
            scroll_rect = pygame.Rect(panel_rect.right - 25, bar_pos, 15, bar_height)
            pygame.draw.rect(self.screen, (180, 180, 180), scroll_rect, border_radius=7)
            pygame.draw.rect(self.screen, (100, 100, 100), scroll_rect, 1, border_radius=7)
    
    def draw_ai_upgrade_panel(self):
        """AI 업그레이드 패널을 화면에 표시합니다."""
        panel_width = 800
        panel_height = 800 # 높이 증가 (기존 750 -> 800)
        panel_x = (self.width - panel_width) // 2
        panel_y = (self.height - panel_height) // 2
        
        # 반투명 오버레이 추가 (전체 화면 어둡게)
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # 어두운 반투명 배경
        self.screen.blit(overlay, (0, 0))
        
        # 패널 배경 (그라데이션 효과 추가)
        panel_surface = pygame.Surface((panel_width, panel_height))
        for y_loop in range(panel_height): # y 변수명 변경 (함수 내 다른 y_offset과 충돌 방지)
            alpha = y_loop / panel_height
            color = (
                int(40 + 10 * alpha),
                int(40 + 15 * alpha),
                int(60 + 20 * alpha)
            )
            pygame.draw.line(panel_surface, color, (0, y_loop), (panel_width, y_loop))
        
        # 패널 테두리
        pygame.draw.rect(panel_surface, (100, 100, 160), (0, 0, panel_width, panel_height), 3, border_radius=10)
        
        # 빛나는 효과 (상단)
        glow_height = 80
        for y_loop in range(glow_height): # y 변수명 변경
            alpha_glow = 100 - (y_loop / glow_height * 100) # alpha 변수명 변경 (함수 내 다른 alpha와 충돌 방지)
            glow_color = (80, 90, 180, int(alpha_glow))
            pygame.draw.line(panel_surface, glow_color, (10, y_loop+5), (panel_width-10, y_loop+5), 2)
        
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        # 제목
        title_font = self.font
        title_text = "AI 전력망 최적화 시스템"
        title_surface = title_font.render(title_text, True, (220, 220, 250))
        title_rect = title_surface.get_rect(centerx=panel_x + panel_width//2, top=panel_y + 20)
        self.screen.blit(title_surface, title_rect)
        
        # 현재 전력망 상태 분석 결과
        analysis_results = getattr(self.drawer, 'current_grid_analysis_results', None)
        if analysis_results:
            overall_sev = analysis_results.get('overall_severity', 0)
            summary_text = analysis_results.get('summary', '전력망 상태 분석 중...')
            
            summary_color_val = (100, 255, 100)
            status_text = "정상"
            if overall_sev >= 0.9: 
                summary_color_val = (255, 100, 100)
                status_text = "심각"
            elif overall_sev >= 0.7: 
                summary_color_val = (255, 150, 50)
                status_text = "경고"
            elif overall_sev >= 0.4: 
                summary_color_val = (255, 220, 50)
                status_text = "주의"
                
            status_rect = pygame.Rect(panel_x + panel_width - 120, panel_y + 30, 100, 40)
            status_surface = pygame.Surface((100, 40))
            status_surface.fill(summary_color_val)
            pygame.draw.rect(status_surface, (255, 255, 255), (0, 0, 100, 40), 2)
            self.screen.blit(status_surface, status_rect)
            
            status_font = self.font
            status_label = status_font.render(status_text, True, (0, 0, 0))
            status_label_rect = status_label.get_rect(center=status_rect.center)
            self.screen.blit(status_label, status_label_rect)
            
            y_offset = panel_y + 80
            
            analysis_header_font = self.font
            analysis_header = analysis_header_font.render("전력망 분석 결과", True, (200, 200, 255))
            analysis_header_rect = analysis_header.get_rect(centerx=panel_x + panel_width//2, top=y_offset)
            self.screen.blit(analysis_header, analysis_header_rect)
            y_offset += analysis_header.get_height() + 5
            
            pygame.draw.line(self.screen, (150, 150, 200), 
                             (panel_x + 50, y_offset), 
                             (panel_x + panel_width - 50, y_offset), 2)
            y_offset += 10
            
            gauge_width = panel_width - 100
            gauge_height = 20
            pygame.draw.rect(self.screen, (80, 80, 100), 
                             (panel_x + 50, y_offset, gauge_width, gauge_height), 0, border_radius=5)
            
            filled_width = int(gauge_width * overall_sev)
            for x_loop in range(filled_width):
                pos = x_loop / gauge_width
                gauge_color = (0,0,0)
                if pos < 0.5: 
                    gauge_color = (int(510 * pos), 255, 0)
                else: 
                    gauge_color = (255, int(255 * (2 - 2 * pos)), 0)
                pygame.draw.line(self.screen, gauge_color, 
                                (panel_x + 50 + x_loop, y_offset), 
                                (panel_x + 50 + x_loop, y_offset + gauge_height), 1)
            
            pygame.draw.rect(self.screen, (200, 200, 200), 
                             (panel_x + 50, y_offset, gauge_width, gauge_height), 2, border_radius=5)
            
            severity_text = f"{overall_sev*100:.1f}%"
            severity_font = self.small_font
            severity_surf = severity_font.render(severity_text, True, (255, 255, 255))
            severity_rect_midright_x = panel_x + 50 + filled_width - 5 if filled_width > 5 else panel_x + 50 + 5 
            severity_rect = severity_surf.get_rect(midright=(severity_rect_midright_x, y_offset + gauge_height//2))
            self.screen.blit(severity_surf, severity_rect)
            
            y_offset += gauge_height + 10
            
            summary_surface = self.font.render(self._truncate_text(summary_text, self.font, panel_width - 60), True, summary_color_val)
            summary_rect = summary_surface.get_rect(centerx=panel_x + panel_width // 2, top=y_offset)
            self.screen.blit(summary_surface, summary_rect)
            y_offset += summary_surface.get_height() + 10
            
            problems = analysis_results.get('problems', [])
            if problems:
                problem_font = self.font
                
                for i, problem in enumerate(problems[:3]):
                    problem_type = problem.get('type', '')
                    problem_severity = problem.get('severity', 0)
                    
                    problem_color_val = (200,200,200)
                    icon_text = "•"
                    if problem_type == 'overloaded_line':
                        problem_color_val = (255, 100, 100) if problem_severity > 0.7 else (255, 180, 50)
                        icon_text = "⚡"
                    elif problem_type == 'blackout_buildings':
                        problem_color_val = (255, 50, 50)
                        icon_text = "⚠️"
                    elif problem_type == 'low_voltage':
                        problem_color_val = (255, 150, 0)
                        icon_text = "↓"
                    elif problem_type == 'overall_shortage':
                         problem_color_val = (255, 100, 50) if problem_severity > 0.6 else (255, 180, 80)
                         icon_text = "📉"
                    elif problem_type == 'low_supply_capacity_margin':
                         problem_color_val = (255, 165, 0)
                         icon_text = "📊"
                    elif problem_type == 'inefficient_producer':
                         problem_color_val = (200, 200, 100)
                         icon_text = "⚙️"

                    icon_surf = problem_font.render(icon_text, True, problem_color_val)
                    icon_rect = icon_surf.get_rect(left=panel_x + 60, top=y_offset)
                    self.screen.blit(icon_surf, icon_rect)
                    
                    description = problem.get('description', '알 수 없는 문제')
                    desc_surf = problem_font.render(
                        self._truncate_text(description, problem_font, panel_width - 140), 
                        True, problem_color_val
                    )
                    desc_rect = desc_surf.get_rect(left=panel_x + 90, top=y_offset)
                    self.screen.blit(desc_surf, desc_rect)
                    
                    y_offset += desc_surf.get_height() + 5
                
                if len(problems) > 3:
                    more_text = f"+ {len(problems) - 3}개 더 많은 문제점..."
                    more_surf = self.small_font.render(more_text, True, (180, 180, 200))
                    more_rect = more_surf.get_rect(centerx=panel_x + panel_width//2, top=y_offset)
                    self.screen.blit(more_surf, more_rect)
                    y_offset += more_surf.get_height() + 8
            
            pygame.draw.line(self.screen, (150, 150, 200), 
                            (panel_x + 50, y_offset), 
                            (panel_x + panel_width - 50, y_offset), 2)
            y_offset += 10
            
            upgrade_header_font = self.font
            upgrade_header = upgrade_header_font.render("추천 업그레이드 옵션", True, (200, 200, 255))
            upgrade_header_rect = upgrade_header.get_rect(centerx=panel_x + panel_width//2, top=y_offset)
            self.screen.blit(upgrade_header, upgrade_header_rect)
            y_offset += upgrade_header.get_height() + 8
            
            budget_font = self.font
            budget_text = f"현재 예산: {self.simulator.budget:.1f}"
            budget_surf = budget_font.render(budget_text, True, (150, 255, 150))
            budget_rect = budget_surf.get_rect(centerx=panel_x + panel_width//2, top=y_offset)
            self.screen.blit(budget_surf, budget_rect)
            y_offset += budget_surf.get_height() + 5 # 여백 10 -> 5
            
            self.drawer.ai_panel_options_start_y = y_offset
        
        if hasattr(self.drawer, 'ai_upgrade_option_buttons'):
            for button in self.drawer.ai_upgrade_option_buttons:
                button.draw(self.screen, self.font)
        
        close_button_size = 30
        close_button_rect = pygame.Rect(panel_x + panel_width - close_button_size - 10, panel_y + 10, close_button_size, close_button_size)
        pygame.draw.rect(self.screen, (150, 70, 70), close_button_rect, 0, border_radius=15)
        pygame.draw.rect(self.screen, (220, 220, 220), close_button_rect, 2, border_radius=15)
        
        pygame.draw.rect(self.screen, (150, 70, 70), close_button_rect, 0, border_radius=15) # 닫기 버튼 색상 변경
        pygame.draw.rect(self.screen, (220, 220, 220), close_button_rect, 2, border_radius=15) # 닫기 버튼 테두리 색상 변경
        
        # X 표시
        pygame.draw.line(self.screen, (255, 255, 255), 
                         (close_button_rect.left + 8, close_button_rect.top + 8), 
                         (close_button_rect.right - 8, close_button_rect.bottom - 8), 3) # X 표시 두께 증가
        pygame.draw.line(self.screen, (255, 255, 255), 
                         (close_button_rect.left + 8, close_button_rect.bottom - 8), 
                         (close_button_rect.right - 8, close_button_rect.top + 8), 3) # X 표시 두께 증가

    def draw_power_plant_menu(self):
        """발전소 타입 선택 메뉴 그리기"""
        if not hasattr(self.drawer.ui_handler, 'power_plant_menu'):
            return
            
        menu = self.drawer.ui_handler.power_plant_menu
        if not menu["visible"]:
            return
        
        # 메뉴 배경 - 기존 UI 아래에 그려지도록 위치 조정
        menu_width = 100
        menu_height = len(menu["buttons"]) * 30 + 10
        menu_x = menu["x"]
        menu_y = 85  # UI 패널 아래쪽에 위치 (기존 버튼들과 겹치지 않게)
        menu_rect = pygame.Rect(menu_x, menu_y, menu_width, menu_height)
        
        # 반투명 배경 그리기
        menu_surface = pygame.Surface((menu_width, menu_height), pygame.SRCALPHA)
        pygame.draw.rect(menu_surface, (40, 40, 40, 230), (0, 0, menu_width, menu_height))
        pygame.draw.rect(menu_surface, (150, 150, 150, 255), (0, 0, menu_width, menu_height), 2)
        self.screen.blit(menu_surface, (menu_x, menu_y))
        
        # 버튼 그리기
        font = pygame.font.Font(self.korean_font_path, 12)
        y_offset = menu_y + 5
        
        for i, button in enumerate(menu["buttons"]):
            button_rect = pygame.Rect(menu_x + 5, y_offset, menu_width - 10, 25)
            
            # 마우스 호버 체크
            mouse_pos = pygame.mouse.get_pos()
            if button_rect.collidepoint(mouse_pos):
                color = (80, 80, 100, 230)
                text_color = (255, 255, 100)
            else:
                color = (60, 60, 60, 200)
                text_color = (220, 220, 220)
            
            # 버튼 배경
            button_surface = pygame.Surface((menu_width - 10, 25), pygame.SRCALPHA)
            pygame.draw.rect(button_surface, color, (0, 0, menu_width - 10, 25))
            pygame.draw.rect(button_surface, (180, 180, 180, 255), (0, 0, menu_width - 10, 25), 1)
            self.screen.blit(button_surface, (menu_x + 5, y_offset))
            
            # 버튼 텍스트
            text = font.render(button["text"], True, text_color)
            text_rect = text.get_rect(center=button_rect.center)
            self.screen.blit(text, text_rect)
            
            # 클릭 영역 저장 (이벤트 처리용)
            button["rect"] = button_rect
            
            y_offset += 30

    def draw_tooltip(self):
        """호버 상태의 건물이나 송전선에 대한 툴팁 표시"""
        if not (self.drawer.hover_bldg or self.drawer.hover_line):
            return
        
        lines = []
        if self.drawer.hover_bldg and not self.drawer.hover_bldg.removed:
            # 건물 툴팁
            b = self.drawer.hover_bldg
            lines.append(("● " + b.get_type_str() + f" {b.idx}", (255, 255, 200)))
            
            # 건물 상세 정보 추가
            if hasattr(b, 'get_detailed_info'):
                detailed_info = b.get_detailed_info()
                # 추가 색상 매핑 (키워드에 따라 다른 색상 적용)
                for info in detailed_info:
                    color = (200, 255, 200)  # 기본 색상
                    
                    # 특정 키워드에 따른 색상 변경
                    if "정전" in info:
                        color = (255, 100, 100)
                    elif "태양광" in info:
                        color = (255, 255, 150)
                    elif "부족" in info:
                        color = (255, 150, 150)
                    elif "배터리" in info:
                        color = (150, 200, 255)
                    
                    lines.append(("  " + info, color))
            else:
                # 기존 방식의 정보 표시 (get_detailed_info가 없는 경우)
                # 소비자 정보 처리 (b.base_supply < 0)
                if b.base_supply < 0:
                    base_demand = abs(b.base_supply)  # 초기 설정된 기본 수요량
                    current_demand = -b.current_supply if b.current_supply < 0 else 0  # 현재 실제 수요량
                    
                    lines.append((f"  기본수요: {base_demand:.1f} MW", (200, 255, 200)))
                    lines.append((f"  현재수요: {current_demand:.1f} MW", (200, 255, 200)))
                    
                    # 태양광 설비 정보 (있으면 표시)
                    if b.solar_capacity > 0:
                        lines.append((f"  태양광설비: {b.solar_capacity:.1f}", (255, 255, 150)))
                    
                    # 부족 정보
                    if hasattr(b, 'shortage'):
                        lines.append((f"  부족: {b.shortage:.1f}", (255, 150, 150)))
                        if b.shortage > 1e-9 and current_demand > 1e-9:
                            shortage_ratio = (b.shortage / current_demand) * 100
                            lines.append((f"  부족률: {shortage_ratio:.1f}%", (255, 150, 150)))
                
                # 생산자 정보 처리 (b.base_supply > 0)
                elif b.base_supply > 0:
                    lines.append((f"  설비용량: {b.base_supply:.1f} MW", (200, 255, 200)))
                    if hasattr(b, 'current_supply') and abs(b.current_supply - b.base_supply) > 1e-9:
                        lines.append((f"  현재출력: {b.current_supply:.1f} MW", (200, 255, 200)))
                    
                    if hasattr(b, 'transmitted_power'):
                        lines.append((f"  송전량: {b.transmitted_power:.1f} MW", (200, 255, 200)))
                        if b.base_supply > 0:
                            utilization = (b.transmitted_power / b.base_supply) * 100
                            lines.append((f"  이용률: {utilization:.1f}%", (150, 200, 255)))
                
                # 중립 건물 등 나머지 경우
                else:  # base_supply == 0
                    lines.append((f"  타입: {b.get_type_str()}", (200, 200, 200)))
                    if b.solar_capacity > 0:
                        lines.append((f"  태양광: {b.solar_capacity:.1f} MW", (255, 255, 150)))
                    if hasattr(b, 'current_supply') and abs(b.current_supply) > 1e-9:
                        lines.append((f"  현재출력: {b.current_supply:.1f} MW", (200, 255, 200)))
                
                # 배터리 정보
                if hasattr(b, 'battery_capacity') and b.battery_capacity > 0:
                    charge_percent = (b.battery_charge / b.battery_capacity) * 100 if b.battery_capacity > 1e-9 else 0
                    lines.append((f"  배터리: {b.battery_charge:.1f}/{b.battery_capacity:.1f} ({charge_percent:.0f}%)", (150, 200, 255)))
                
                # 정전 정보
                if b.blackout:
                    lines.append(("  ⚠ 정전!", (255, 100, 100)))
        
        elif self.drawer.hover_line and not self.drawer.hover_line.removed:
            # 송전선 툴팁
            pl = self.drawer.hover_line
            cap = pl.capacity
            f = pl.flow
            usage = 0 if cap < 1e-9 else abs(f) / cap
            lines.append(("● 송전선 정보", (255, 255, 200)))
            lines.append((f"  연결: {pl.u} → {pl.v}", (220, 220, 255)))
            lines.append((f"  최대 용량: {cap:.1f}", (200, 255, 200)))
            lines.append((f"  현재 흐름: {f:+.1f}", (200, 255, 200)))
            usage_color = (150, 255, 150) if usage < 0.5 else (255, 255, 150) if usage < 0.8 else (255, 150, 150)
            lines.append((f"  사용률: {usage*100:.1f}%", usage_color))
            
            # 과부하 경고
            if usage > 0.8:
                lines.append(("  ⚠ 과부하 위험!", (255, 100, 100)))
            
            # 비용 정보
            lines.append((f"  설치 비용: {pl.cost:.1f}", (200, 200, 255)))
            
            # 현재 상태
            if usage < 0.3:
                status = "여유"
                status_color = (150, 255, 150)
            elif usage < 0.7:
                status = "정상"
                status_color = (220, 220, 150)
            elif usage < 0.9:
                status = "부하"
                status_color = (255, 200, 100)
            else:
                status = "위험"
                status_color = (255, 100, 100)
            lines.append((f"  상태: {status}", status_color))
        
        if not lines:
            return
        
        # 툴팁 크기 계산
        margin = 8
        padding = 10
        line_padding = 2
        lineh = 24
        
        w = max(self.small_font.size(text)[0] for text, _ in lines) + padding * 2
        h = len(lines) * lineh + (len(lines) - 1) * line_padding + padding * 2
        
        # 툴팁 위치 조정
        mx, my = pygame.mouse.get_pos()
        tooltip_x = mx + margin
        tooltip_y = my + margin
        if tooltip_x + w > self.width - margin:
            tooltip_x = mx - w - margin
        if tooltip_y + h > self.height - margin:
            tooltip_y = my - h - margin
        
        # 그림자 효과
        shadow_offset = 3
        shadow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (0, 0, 0, 60), shadow.get_rect(), border_radius=8)
        self.screen.blit(shadow, (tooltip_x + shadow_offset, tooltip_y + shadow_offset))
        
        # 배경 그라데이션
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        gradient_top = (60, 60, 80, 255)
        gradient_bottom = (40, 40, 60, 255)
        for y in range(h):
            alpha = y / h
            color = [int(gradient_top[i] * (1 - alpha) + gradient_bottom[i] * alpha) for i in range(4)]
            pygame.draw.line(surf, color, (0, y), (w, y))
        
        # 테두리
        pygame.draw.rect(surf, (255, 255, 255, 50), surf.get_rect(), border_radius=8)
        
        # 텍스트 그리기
        y = padding
        for text, color in lines:
            txt_surf = self.small_font.render(text, True, color)
            txt_rect = txt_surf.get_rect(x=padding, y=y)
            surf.blit(txt_surf, txt_rect)
            y += lineh + line_padding
        
        # 화면에 그리기
        self.screen.blit(surf, (tooltip_x, tooltip_y)) 