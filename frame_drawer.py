import pygame
import math
class FrameDrawer:
    def __init__(self, simulator):
        self.simulator = simulator
    
    def draw_arrow(screen,x1,y1,x2,y2,color,width=2):
        pygame.draw.line(screen,color,(x1,y1),(x2,y2),width)
        angle=math.atan2(y2-y1,x2-x1)
        arr_size=10+width
        ang_l=angle+math.pi*0.75
        ang_r=angle-math.pi*0.75
        lx=x2+arr_size*math.cos(ang_l)
        ly=y2+arr_size*math.sin(ang_l)
        rx=x2+arr_size*math.cos(ang_r)
        ry=y2+arr_size*math.sin(ang_r)
        pygame.draw.polygon(screen,color,[(x2,y2),(lx,ly),(rx,ry)])

    def draw_city_background(screen, width, height):
        # 먼저 기존처럼 그라디언트를 깔고,
        top_color=(150,200,255)
        bottom_color=(230,230,255)
        for y in range(height):
            alpha=y/float(height)
            r=int(top_color[0]*(1-alpha)+bottom_color[0]*alpha)
            g=int(top_color[1]*(1-alpha)+bottom_color[1]*alpha)
            b=int(top_color[2]*(1-alpha)+bottom_color[2]*alpha)
            pygame.draw.line(screen,(r,g,b),(0,y),(width,y))


    def draw_frame(self, partial=False):
        # 배경
        self.draw_city_background(self.simulator.screen, self.simulator.width, self.simulator.height)
        
        # 송전선 추가 모드에서 임시 선
        if self.simulator.add_mode=="add_line" and self.simulator.temp_line_start:
            mx,my = pygame.mouse.get_pos()
            start_x, start_y = self.simulator.world_to_screen(self.simulator.temp_line_start.x, self.simulator.temp_line_start.y)
            dash_length = 10
            space_length = 5
            total_length = math.hypot(mx-start_x, my-start_y)
            angle = math.atan2(my-start_y, mx-start_x)
            dash_count = int(total_length / (dash_length + space_length))
            for i in range(dash_count):
                start_dist = i*(dash_length+space_length)
                end_dist = start_dist + dash_length
                if end_dist>total_length:
                    end_dist=total_length
                dash_start_x = start_x + math.cos(angle)*start_dist
                dash_start_y = start_y + math.sin(angle)*start_dist
                dash_end_x   = start_x + math.cos(angle)*end_dist
                dash_end_y   = start_y + math.sin(angle)*end_dist
                pygame.draw.line(self.simulator.screen, (255,255,100),
                                 (dash_start_x,dash_start_y),
                                 (dash_end_x,dash_end_y), 2)
        
        # 송전선
        for pl in self.simulator.city.lines:
            if pl.removed:
                continue
            if self.simulator.city.buildings[pl.u].removed or self.simulator.city.buildings[pl.v].removed:
                continue
            x1 = self.simulator.city.buildings[pl.u].x
            y1 = self.simulator.city.buildings[pl.u].y
            x2 = self.simulator.city.buildings[pl.v].x
            y2 = self.simulator.city.buildings[pl.v].y
            sx1,sy1 = self.simulator.world_to_screen(x1,y1)
            sx2,sy2 = self.simulator.world_to_screen(x2,y2)
            
            usage = 0
            if pl.capacity>1e-9:
                usage = abs(pl.flow)/pl.capacity
                if usage>1:
                    usage=1
            r = int(200*usage)
            g = int(200*(1-usage))
            color = (r,g,0)
            thick = max(3, int(3 + 7*usage))
            
            # 파티클 생성
            if abs(pl.flow) > 0.1:  # 의미있는 전력 흐름이 있을 때만
                b_start = self.simulator.city.buildings[pl.u]
                b_end = self.simulator.city.buildings[pl.v]
                self.simulator.particles.spawn_particles_for_line(pl, b_start, b_end, self.simulator.clock.get_time())
            
            # 글로우 효과
            if usage>0.2:
                glow_surf = pygame.Surface((self.simulator.width,self.simulator.height), pygame.SRCALPHA)
                glow_col = (r,g,0,80)
                pygame.draw.line(glow_surf, glow_col, (sx1,sy1), (sx2,sy2), thick+8)
                self.simulator.screen.blit(glow_surf, (0,0))
            
            # 메인 라인
            pygame.draw.line(self.simulator.screen, color, (sx1,sy1), (sx2,sy2), thick)
            if abs(pl.flow)>0.1:
                if pl.flow>0:
                    self.draw_arrow(self.simulator.screen, sx1, sy1, sx2, sy2, color, thick)
                else:
                    self.draw_arrow(self.simulator.screen, sx2, sy2, sx1, sy1, color, thick)
            
            # 중간 정보 박스
            mid_x = (sx1 + sx2)/2
            mid_y = (sy1 + sy2)/2
            info_color = (0,200,0) if usage<0.5 else (200,200,0) if usage<0.8 else (200,0,0)
            usage_percent = usage*100
            flow_text = f"{abs(pl.flow):.1f}/{pl.capacity:.1f}"
            usage_text = f"{usage_percent:.0f}%"
            if usage>0.8:
                warning = "⚠" if usage>0.95 else "!"
                flow_text = warning + " " + flow_text
            
            def render_text_with_shadow(text, color):
                shadow_surf = self.simulator.small_font.render(text, True, (0,0,0))
                text_surf = self.simulator.small_font.render(text, True, color)
                combined = pygame.Surface((text_surf.get_width()+2, text_surf.get_height()+2), pygame.SRCALPHA)
                combined.blit(shadow_surf, (2,2))
                combined.blit(text_surf, (0,0))
                return combined
            
            flow_surf = render_text_with_shadow(flow_text, info_color)
            usage_surf = render_text_with_shadow(usage_text, info_color)
            
            padding = 4
            margin = 2
            box_width = max(flow_surf.get_width(), usage_surf.get_width()) + padding*2
            box_height = flow_surf.get_height() + usage_surf.get_height() + padding*2 + margin
            box = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
            box.fill((0,0,0,160))
            
            flow_x = (box_width - flow_surf.get_width()) / 2
            usage_x = (box_width - usage_surf.get_width()) / 2
            box.blit(flow_surf, (flow_x, padding))
            box.blit(usage_surf, (usage_x, padding + flow_surf.get_height()+margin))
            
            box_x = mid_x - box_width/2
            box_y = mid_y - box_height/2
            if box_x<0: box_x=0
            if box_y<0: box_y=0
            if box_x+box_width>self.simulator.width: box_x = self.simulator.width - box_width
            if box_y+box_height>self.simulator.height: box_y = self.simulator.height - box_height
            self.simulator.screen.blit(box, (box_x, box_y))
        
        # 파티클
        self.simulator.particles.draw(self.simulator.screen, self)
        
        # 건물
        for b in self.simulator.city.buildings:
            if b.removed:
                continue
            self.simulator.draw_building(b)
        
        # UI 패널
        panel_surf = pygame.Surface((self.simulator.ui_rect.width, self.simulator.ui_rect.height))
        color_top = (170,170,210)
        color_bottom = (130,130,180)
        for y in range(self.simulator.ui_rect.height):
            alpha = y/float(self.simulator.ui_rect.height)
            rr = int(color_top[0]*(1-alpha) + color_bottom[0]*alpha)
            gg = int(color_top[1]*(1-alpha) + color_bottom[1]*alpha)
            bb = int(color_top[2]*(1-alpha) + color_bottom[2]*alpha)
            pygame.draw.line(panel_surf, (rr,gg,bb), (0,y), (self.simulator.ui_rect.width,y))
        self.simulator.screen.blit(panel_surf, (self.simulator.ui_rect.x, self.simulator.ui_rect.y))
        
        pygame.draw.rect(self.simulator.screen, (50,50,50), self.simulator.ui_rect, 2, border_radius=10)
        for b in self.simulator.buttons:
            b.draw(self.simulator.screen, self.simulator.font)
        
        # 전력 공급 상황
        flow_val = self.simulator.calc_total_flow()
        dem = self.simulator.city.total_demand()
        
        # 정전된 건물 확인
        blackout_buildings = []
        affected_demand = 0
        for b in self.simulator.city.buildings:
            if not b.removed and b.blackout:
                blackout_buildings.append(b)
                affected_demand += abs(b.base_supply)  # 음수값이므로 절대값 취함

        if blackout_buildings or flow_val+1e-9 < dem:
            shortage = dem - flow_val
            shortage_percent = (shortage/dem)*100
            
            if len(blackout_buildings) > 0:
                status_color = (255, 0, 0)
                status_text = "매우 심각한 전력 부족"
                blink = True
            elif shortage_percent <= 10:
                status_color = (255, 200, 0)
                status_text = "전력 부족"
                blink = False
            elif shortage_percent <= 30:
                status_color = (255, 100, 0)
                status_text = "심각한 전력 부족"
                blink = True
            else:
                status_color = (255, 0, 0)
                status_text = "매우 심각한 전력 부족"
                blink = True
            
            if not blink or (pygame.time.get_ticks() // 500) % 2:
                blackout_info = ""
                if blackout_buildings:
                    blackout_info = f" | 정전 건물: {len(blackout_buildings)}개 (영향 수요: {affected_demand:.1f})"
                txt = f"{status_text}! (공급 {flow_val:.1f} < 수요 {dem:.1f}, 부족률 {shortage_percent:.1f}%{blackout_info})"
                surf = self.simulator.big_font.render(txt, True, status_color)
                shadow_surf = self.simulator.big_font.render(txt, True, (0,0,0))
                rect = surf.get_rect(center=(self.simulator.width//2, 40))
                if shortage_percent > 30 or blackout_buildings:
                    scale = 1.1
                    surf = pygame.transform.scale(surf, (int(rect.width*scale), int(rect.height*scale)))
                    shadow_surf = pygame.transform.scale(shadow_surf, (int(rect.width*scale), int(rect.height*scale)))
                    rect = surf.get_rect(center=(self.simulator.width//2, 40))
                self.simulator.screen.blit(shadow_surf, (rect.x+2, rect.y+2))
                self.simulator.screen.blit(surf, rect)
                if shortage_percent > 30 or blackout_buildings:
                    warning_txt = "⚠ 즉시 조치가 필요합니다!"
                    warning_surf = self.simulator.font.render(warning_txt, True, (255,0,0))
                    warning_rect = warning_surf.get_rect(center=(self.simulator.width//2, 80))
                    self.simulator.screen.blit(warning_surf, warning_rect)
        else:
            txt = f"정상 공급 (공급 {flow_val:.1f} / 수요 {dem:.1f})"
            surf = self.simulator.big_font.render(txt, True, (0,100,0))
            shadow_surf = self.simulator.big_font.render(txt, True, (0,0,0))
            rect = surf.get_rect(center=(self.simulator.width//2,40))
            self.simulator.screen.blit(shadow_surf, (rect.x+2, rect.y+2))
            self.simulator.screen.blit(surf, rect)
        
        mode_txt = f"모드: {self.simulator.add_mode}"
        ms = self.simulator.font.render(mode_txt, True, (0,0,0))
        self.simulator.screen.blit(ms, (self.simulator.width-self.simulator.panel_width+20, self.simulator.height-120))
        
        bd_txt = f"예산: {self.simulator.budget:.1f}, 자금: {self.simulator.money:.1f}"
        bs = self.simulator.font.render(bd_txt, True, (0,0,100))
        self.simulator.screen.blit(bs, (self.simulator.width-self.simulator.panel_width+20, self.simulator.height-60))
        
        # 시간/날씨 표시
        weekday_kr = ["월","화","수","목","금","토","일"]
        season = self.simulator.get_current_season()
        time_str = self.simulator.simTime.strftime("%Y-%m-%d %H:%M")
        wday = weekday_kr[self.simulator.simTime.weekday()]
        
        icon_map = {
            "맑음":"☀",
            "흐림":"☁",
            "비":"🌧",
            "눈":"❄"
        }
        wicon = icon_map.get(self.simulator.current_weather, "☀")
        
        kr_time = f"{time_str} ({wday}) [{season}] {wicon}"
        ts = self.simulator.font.render(f"시간: {kr_time}", True, (0,0,0))
        shadow_ts = self.simulator.font.render(f"시간: {kr_time}", True, (255,255,255))
        self.simulator.screen.blit(shadow_ts, (11,11))
        self.simulator.screen.blit(ts, (10,10))
        
        weather_info = (
            f"날씨: {self.simulator.current_weather}\n"
            f"기온: {self.simulator.current_temperature:.1f}°C\n"
            f"습도: {self.simulator.humidity:.1f}%\n"
            f"구름: {self.simulator.cloud_factor*100:.0f}%\n"
            f"태양광: {self.simulator.solar_efficiency*100:.2f}%"
        )
        
        # 멀티라인 텍스트 렌더링
        y_offset = 40
        for line in weather_info.split('\n'):
            ws = self.simulator.font.render(line, True, (0,0,0))
            shadow_ws = self.simulator.font.render(line, True, (255,255,255))
            self.simulator.screen.blit(shadow_ws, (11, y_offset+1))
            self.simulator.screen.blit(ws, (10, y_offset))
            y_offset += 30
        
        if not partial:
            if self.simulator.show_help:
                self.simulator.draw_help_overlay()
            if self.simulator.show_scenario_list:
                self.simulator.draw_scenario_list()
            self.simulator.draw_tooltip()
            self.simulator.context_menu.draw(self.simulator.screen)
   
