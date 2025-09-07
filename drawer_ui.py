import pygame
import math
from utils import *
from uis import *
from city import PowerLine
from algorithms import simple_upgrade_ai, analyze_current_grid_status, upgrade_critical_lines, build_producer_in_needed_area

class DrawerUI:
    def __init__(self, drawer):
        self.drawer = drawer
        self.simulator = drawer.simulator
        self.ai_upgrade_option_buttons = []
    
    def setup_buttons(self):
        """버튼 설정 초기화"""
        # UI 패널 너비: 380px
        # 버튼을 패널 안에 더 크게 배치
        panel_right = self.drawer.width  # 패널 오른쪽 끝
        panel_left = self.drawer.width - self.drawer.panel_width  # 패널 왼쪽 시작
        
        # 버튼 크기를 패널에 맞게 크게 조정
        button_width = 170  # 버튼 너비를 크게 늘림
        button_height = 40  # 버튼 높이도 늘림
        button_spacing = 5  # 간격
        padding = 10  # 패널 가장자리 여백
        
        # 버튼을 두 열로 배치
        col1_x = panel_left + padding
        col2_x = panel_left + padding + button_width + 10
        button_y_start = 50  # 상단 여백
        
        # 버튼들을 우측 패널 안에 두 열로 정렬
        self.drawer.buttons = [
            # 첫 번째 열 - 모드와 건물
            {"text": "일반모드", "x": col1_x, "y": button_y_start, "width": button_width, "height": button_height, "color": (100, 150, 200), "action": lambda: self.drawer.set_mode("normal")},
            {"text": "삭제모드", "x": col1_x, "y": button_y_start + (button_height + button_spacing) * 1, "width": button_width, "height": button_height, "color": (200, 100, 100), "action": lambda: self.drawer.set_mode("delete")},
            {"text": "수요처", "x": col1_x, "y": button_y_start + (button_height + button_spacing) * 2, "width": button_width, "height": button_height, "color": (150, 200, 150), "action": lambda: self.start_add_building("house")},
            {"text": "상가", "x": col1_x, "y": button_y_start + (button_height + button_spacing) * 3, "width": button_width, "height": button_height, "color": (200, 150, 100), "action": lambda: self.start_add_building("shop")},
            {"text": "송전선", "x": col1_x, "y": button_y_start + (button_height + button_spacing) * 4, "width": button_width, "height": button_height, "color": (100, 100, 200), "action": lambda: self.start_add_line()},
            {"text": "🛤️선 꺾기", "x": col1_x, "y": button_y_start + (button_height + button_spacing) * 5, "width": button_width, "height": button_height, "color": (255, 165, 0), "action": lambda: self.start_add_junction()},
            {"text": "복구", "x": col1_x, "y": button_y_start + (button_height + button_spacing) * 6, "width": button_width, "height": button_height, "color": (100, 200, 100), "action": self.restore_all},
            
            # 두 번째 열 - 발전소와 기능
            {"text": "풍력", "x": col2_x, "y": button_y_start, "width": button_width, "height": button_height, "color": (100, 200, 255), "action": lambda: self.start_add_power_plant("wind", 80)},
            {"text": "태양광", "x": col2_x, "y": button_y_start + (button_height + button_spacing) * 1, "width": button_width, "height": button_height, "color": (255, 200, 50), "action": lambda: self.start_add_power_plant("solar", 60)},
            {"text": "수력", "x": col2_x, "y": button_y_start + (button_height + button_spacing) * 2, "width": button_width, "height": button_height, "color": (50, 150, 255), "action": lambda: self.start_add_power_plant("hydro", 100)},
            {"text": "원자력", "x": col2_x, "y": button_y_start + (button_height + button_spacing) * 3, "width": button_width, "height": button_height, "color": (255, 100, 100), "action": lambda: self.start_add_power_plant("nuclear", 200)},
            {"text": "화력", "x": col2_x, "y": button_y_start + (button_height + button_spacing) * 4, "width": button_width, "height": button_height, "color": (120, 80, 60), "action": lambda: self.start_add_power_plant("thermal", 150)},
            {"text": "수소저장", "x": col2_x, "y": button_y_start + (button_height + button_spacing) * 5, "width": button_width, "height": button_height, "color": (200, 100, 255), "action": lambda: self.start_add_power_plant("hydrogen", 100)},
            {"text": "AI업그레이드", "x": col2_x, "y": button_y_start + (button_height + button_spacing) * 6, "width": button_width, "height": button_height, "color": (200, 100, 200), "action": self.toggle_ai_upgrade},
            {"text": "시나리오", "x": col2_x, "y": button_y_start + (button_height + button_spacing) * 7, "width": button_width, "height": button_height, "color": (200, 200, 100), "action": self.toggle_scenario_list},
        ]
        
        # 선택된 발전소 타입
        self.selected_power_plant_type = None
        self.selected_power_capacity = 0
    
    def toggle_scenario_list(self):
        """시나리오 목록 표시 토글"""
        self.drawer.show_scenario_list = not self.drawer.show_scenario_list
    
    def restore_all(self):
        """모든 건물과 송전선 복원"""
        self.simulator.city.restore_all()
        self.simulator.update_flow(instant=True)

    def toggle_ai_upgrade(self):
        """AI 업그레이드 패널 토글"""
        if self.drawer.show_ai_upgrade_panel:
            self.drawer.show_ai_upgrade_panel = False
            self.ai_upgrade_option_buttons = []
        else:
            self.ai_upgrade()
    
    def cycle_scenario(self):
        """시나리오 순환"""
        if hasattr(self.simulator, 'scenarios') and self.simulator.scenarios:
            current_idx = 0
            if hasattr(self.simulator, 'current_scenario_index'):
                current_idx = (self.simulator.current_scenario_index + 1) % len(self.simulator.scenarios)
            else:
                current_idx = 0
            
            # 다음 시나리오 로드
            self.simulator.current_scenario_index = current_idx
            scenario = self.simulator.scenarios[current_idx]
            self.simulator.load_scenario(scenario)
            print(f"시나리오 변경: {scenario.get('name', '이름 없음')}")
    
    def start_normal_mode(self):
        """일반 모드로 전환"""
        self.drawer.add_mode = "none"
        self.drawer.temp_line_start = None
        # waypoint 편집 상태 초기화
        self.drawer.waypoint_mode = False
        self.drawer.editing_line = None
        self.drawer.temp_waypoints = []
        self.drawer.dragging_waypoint = False
        self.drawer.dragging_waypoint_index = -1
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    
    def start_delete_mode(self):
        """삭제 모드로 전환"""
        self.drawer.add_mode = "delete"
        self.drawer.temp_line_start = None
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_NO)
    
    def start_add_building(self, building_type):
        """건물 추가 모드로 전환"""
        if building_type == "house":
            self.drawer.add_mode = "add_demand"
        elif building_type == "shop":
            self.drawer.add_mode = "add_shop"
        else:
            self.drawer.add_mode = "add_neutral"
        self.drawer.temp_line_start = None
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
    
    def start_add_junction(self):
        """waypoint 편집 모드로 전환"""
        print("=" * 50)
        print("🛤️ 송전선 꺾기 모드 시작!")
        print("1️⃣ 먼저 꺾고 싶은 송전선을 클릭하세요")
        print("2️⃣ 송전선 위의 원하는 지점을 클릭해서 꺾임점 추가")
        print("3️⃣ Enter 키로 저장, ESC 키로 취소")
        print("=" * 50)
        
        # 송전선 선택 모드로 전환
        self.drawer.add_mode = "select_line_for_waypoint"
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
        
        # 사용 가능한 송전선 개수 출력
        available_lines = len([l for l in self.simulator.city.lines if not l.removed])
        print(f"📍 편집 가능한 송전선: {available_lines}개")
    

    def start_add_power_plant(self, plant_type, capacity):
        """특정 타입의 발전소 추가 모드로 전환"""
        self.selected_power_plant_type = plant_type
        self.selected_power_capacity = capacity
        self.drawer.add_mode = "add_power_plant"
        self.drawer.temp_line_start = None
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)


    
    def start_add_demand(self):
        """수요 건물 추가 모드로 전환"""
        self.drawer.add_mode = "add_demand"
        self.drawer.temp_line_start = None
    
    def start_add_neutral(self):
        """중립 건물 추가 모드로 전환"""
        self.drawer.add_mode = "add_neutral"
        self.drawer.temp_line_start = None
    
    def start_add_line(self):
        """송전선 추가 모드로 전환"""
        self.drawer.add_mode = "add_line"
        self.drawer.temp_line_start = None
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_CROSSHAIR)
    
    def finish_add_line(self):
        """송전선 추가 모드 종료"""
        self.drawer.add_mode = "none"
        self.drawer.temp_line_start = None
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        self.simulator.update_flow(instant=True)
    
    def toggle_waypoint_mode(self):
        """송전선 waypoint 편집 모드 토글"""
        if not self.drawer.waypoint_mode:
            # waypoint 모드 시작
            self.drawer.waypoint_mode = True
            self.drawer.add_mode = "waypoint"
            self.drawer.editing_line = None
            self.drawer.temp_waypoints = []
        else:
            # waypoint 모드 종료
            if self.drawer.editing_line and self.drawer.temp_waypoints:
                # 임시 waypoint를 실제 송전선에 적용
                self.drawer.editing_line.waypoints = self.drawer.temp_waypoints.copy()
            self.drawer.waypoint_mode = False
            self.drawer.add_mode = "none"
            self.drawer.editing_line = None
            self.drawer.temp_waypoints = []
    
    def ai_upgrade(self):
        """AI 자동 업그레이드 실행 -> 패널 표시로 변경"""
        self.drawer.show_ai_upgrade_panel = True
        if hasattr(self.simulator, 'pause_simulation'):
            self.simulator.pause_simulation()
        else:
            # print("[경고] Simulator에 pause_simulation 기능이 없어 시간이 계속 흐릅니다.")
            pass
        
        # 향상된 분석 결과 가져오기
        analysis_output = analyze_current_grid_status(self.simulator)
        # DrawerRenderer에서 사용할 수 있도록 Drawer 객체에 저장
        self.drawer.current_grid_analysis_results = analysis_output 
        # 기존 current_grid_analysis_text는 직접 사용하지 않거나, 여기서 채울 수 있음 (일단 results 전체를 넘김)

        # print(f"AI 업그레이드 패널 표시. 분석 요약: {analysis_output.get('summary', 'N/A')}")
        self.setup_ai_upgrade_buttons() # 버튼 설정은 분석 결과 이후에 호출 (나중에 동적 생성 위해)
    
    def setup_ai_upgrade_buttons(self):
        """AI 업그레이드 패널의 선택지 버튼들을 생성합니다. 전력망 분석 결과에 따라 맞춤형 옵션을 제공합니다."""
        self.ai_upgrade_option_buttons.clear()
        
        panel_width = 800 
        panel_height = 600 
        panel_x = (self.drawer.width - panel_width) // 2
        panel_screen_y_start = (self.drawer.height - panel_height) // 2 # 패널이 화면에 그려지는 실제 Y 시작점
        
        # 버튼 시작 Y 좌표를 drawer_render.py에서 계산된 값으로 설정
        # fallback 값을 좀 더 합리적으로 수정합니다.
        # 패널 상단부터 약 300px 아래에서 버튼이 시작되도록 초기값 설정 (타이틀, 분석결과 등 공간 고려)
        default_button_start_y_offset = 300 # 기존 360에서 300으로 수정
        button_start_y = getattr(self.drawer, 'ai_panel_options_start_y', panel_screen_y_start + default_button_start_y_offset)
        
        button_width = panel_width - 80
        button_height = 40
        button_padding = 15
        
        # 텍스트 잘라내기를 위한 준비 (DrawerRenderer의 _truncate_text와 Drawer의 font 사용)
        # DrawerUI는 self.drawer를 통해 Drawer 인스턴스에 접근 가능
        # Drawer 인스턴스는 renderer와 font 속성을 가지고 있다고 가정합니다.
        truncate_func = self.drawer._truncate_text if hasattr(self.drawer, '_truncate_text') else None
        current_font = self.drawer.font if hasattr(self.drawer, 'font') else pygame.font.Font(None, 24) # Fallback font
        # benefit_font = self.drawer.small_font if hasattr(self.drawer, 'small_font') else pygame.font.Font(None, 20)

        # 전력망 분석 결과 가져오기
        analysis_results = getattr(self.drawer, 'current_grid_analysis_results', None)
        grid_problems = analysis_results.get('problems', []) if analysis_results else []
        overall_severity = analysis_results.get('overall_severity', 0) if analysis_results else 0
        
        # 도시 및 전력망 데이터 가져오기
        city = self.simulator.city
        
        # 업그레이드 옵션 생성
        upgrade_options = []
        
        # 1. 송전선 관련 옵션 (항상 사용률이 가장 높은 송전선 타겟팅)
        target_line_info = "없음"
        best_line = None
        best_usage_rate = 0
        second_best_line = None
        second_usage_rate = 0
        
        if hasattr(city, 'lines'):
            # 사용률 기준 상위 2개 송전선 찾기
            for line in city.lines:
                if not line.removed and line.capacity > 1e-9:
                    usage_rate = (abs(line.flow) / line.capacity)
                    if usage_rate > best_usage_rate:
                        second_best_line = best_line
                        second_usage_rate = best_usage_rate
                        best_line = line
                        best_usage_rate = usage_rate
                    elif usage_rate > second_usage_rate:
                        second_best_line = line
                        second_usage_rate = usage_rate
        
        if best_line:
            target_line_info = f"송전선 {best_line.u}-{best_line.v} (사용률: {best_usage_rate*100:.1f}%)"
            
            # 과부하 송전선이 있는지 확인
            overloaded = best_usage_rate > 0.8
            
            # 첫 번째 옵션: 가장 부하가 높은 송전선 용량 증설
            option_text = f"가장 부하가 높은 {target_line_info} 용량 증설"
            if overloaded:
                option_text = f"⚠️ 과부하 {target_line_info} 용량 증설 (긴급)"
            
            expected_benefit = f"송전 용량 +{max(2.0, best_line.capacity * 0.2):.1f} 증가, 사용률 {best_usage_rate*100:.1f}% → {(best_usage_rate * best_line.capacity / (best_line.capacity + max(2.0, best_line.capacity * 0.2)) * 100):.1f}%"
            
            priority = 3  # 기본 우선순위
            if overloaded:
                priority = 1  # 과부하 상태면 최우선
            
            upgrade_options.append({
                "id": "upgrade_line",
                "text": option_text,
                "cost": 50,
                "priority": priority,
                "category": "송전",
                "target_data": {"line": best_line, "usage_rate": best_usage_rate},
                "benefit": expected_benefit
            })
            
            # 복수 송전선 동시 업그레이드 옵션 (두 번째로 부하 높은 송전선이 있을 경우)
            if second_best_line and second_usage_rate > 0.6:  # 60% 이상인 경우만
                second_target_info = f"송전선 {second_best_line.u}-{second_best_line.v} (사용률: {second_usage_rate*100:.1f}%)"
                
                # 복수 송전선 동시 업그레이드 옵션
                option_text = f"다중 송전선 용량 증설 ({target_line_info} 및 {second_target_info})"
                expected_benefit = f"주요 과부하 송전선 2개의 용량 동시 증설 (전체 네트워크 안정성 향상)"
                
                upgrade_options.append({
                    "id": "upgrade_multiple_lines",
                    "text": option_text,
                    "cost": 90,  # 단일 송전선보다 더 높은 비용
                    "priority": 2,  # 우선순위는 단일 과부하 송전선 다음
                    "category": "송전",
                    "target_data": {"lines": [best_line, second_best_line]},
                    "benefit": expected_benefit
                })
        
        # 2. 발전소 추가 옵션
        # 수요가 가장 높은 지역 또는 정전 지역 근처에 발전소 건설
        blackout_areas = []
        high_demand_areas = []
        
        # 정전 지역 확인
        if hasattr(self.simulator.power_system, 'blackout_buildings'):
            for b in self.simulator.power_system.blackout_buildings:
                if not b.removed:
                    blackout_areas.append(b)
        
        # 수요가 높은 지역 확인
        for b in city.buildings:
            if not b.removed and b.base_supply < -8:  # 기준값 임의 설정, 조정 가능
                high_demand_areas.append(b)
        
        # 발전소 건설 옵션
        if blackout_areas:
            # 정전 지역이 있으면 발전소 건설 옵션
            target_area = max(blackout_areas, key=lambda b: getattr(b, 'shortage', 0) if hasattr(b, 'shortage') else 0)
            area_name = getattr(target_area, 'name', f"건물 {target_area.idx}")
            option_text = f"⚠️ 정전 지역 ({area_name}) 인근 발전소 건설 (긴급)"
            
            upgrade_options.append({
                "id": "build_producer",
                "text": option_text,
                "cost": 100,
                "priority": 1,  # 정전 해소는 최우선
                "category": "발전",
                "target_data": {"building": target_area},
                "benefit": "정전 지역에 15.0 용량의 발전소 건설로 전력 공급 정상화"
            })
        elif high_demand_areas:
            # 수요가 높은 지역이 있으면 발전소 건설 옵션
            target_area = max(high_demand_areas, key=lambda b: abs(b.base_supply))
            area_name = getattr(target_area, 'name', f"건물 {target_area.idx}")
            option_text = f"고수요 지역 ({area_name}, 수요: {abs(target_area.base_supply):.1f}) 인근 발전소 건설"
            
            upgrade_options.append({
                "id": "build_producer",
                "text": option_text,
                "cost": 100,
                "priority": 2,
                "category": "발전",
                "target_data": {"building": target_area},
                "benefit": "수요 집중 지역 근처에 15.0 용량의 발전소 건설로 송전 부하 분산"
            })
        else:
            # 일반적인 발전소 건설 옵션
            option_text = "전략적 위치에 발전소 건설"
            
            upgrade_options.append({
                "id": "build_producer",
                "text": option_text,
                "cost": 100,
                "priority": 3,
                "category": "발전",
                "target_data": {},
                "benefit": "전력망 중심부에 15.0 용량의 발전소 건설로 전력 공급 강화"
            })
        
        # 3. 태양광 설비 개선 옵션
        # 태양광 설비가 있는 건물 또는 태양광 설치 가능한 건물 확인
        buildings_with_solar = [b for b in city.buildings if not b.removed and b.solar_capacity > 0]
        candidate_buildings = [b for b in city.buildings if not b.removed and b.base_supply <= 0 and b.solar_capacity == 0]
        
        if candidate_buildings:
            # 태양광 설치 옵션
            upgrade_options.append({
                "id": "add_solar",
                "text": f"수요 건물에 태양광 발전 설비 설치 (자체 발전 강화)",
                "cost": 60,
                "priority": 3,
                "category": "신재생",
                "target_data": {"buildings": candidate_buildings[:3]},  # 최대 3개 건물 선택
                "benefit": "선택된 건물들에 태양광 패널 설치로 일조량에 따라 최대 5.0의 자체 발전"
            })
        
        if buildings_with_solar:
            # 기존 태양광 업그레이드 옵션
            upgrade_options.append({
                "id": "upgrade_solar",
                "text": f"기존 태양광 설비 업그레이드 (효율 향상)",
                "cost": 40,
                "priority": 4,
                "category": "신재생",
                "target_data": {"buildings": buildings_with_solar[:3]},
                "benefit": "기존 태양광 설비 용량 50% 증가로 발전 효율 향상"
            })
        
        # 4. 배터리 관련 옵션
        # 배터리가 있는 건물 또는 배터리 설치 가능한 건물 확인
        buildings_with_battery = [b for b in city.buildings if not b.removed and hasattr(b, 'battery_capacity') and b.battery_capacity > 0]
        
        # 배터리 설치/업그레이드 옵션
        if len(buildings_with_battery) < 3:  # 배터리가 적으면 신규 설치 옵션
            upgrade_options.append({
                "id": "add_battery",
                "text": "주요 건물에 에너지 저장 시스템(ESS) 설치",
                "cost": 70,
                "priority": 3,
                "category": "저장",
                "target_data": {},
                "benefit": "피크 시간대 전력 수요 분산 및 태양광 발전 효율 극대화 (10.0 용량 배터리 설치)"
            })
        elif buildings_with_battery:  # 배터리가 이미 있으면 업그레이드 옵션
            upgrade_options.append({
                "id": "upgrade_battery",
                "text": "기존 에너지 저장 시스템(ESS) 용량 확장",
                "cost": 50,
                "priority": 4,
                "category": "저장",
                "target_data": {"buildings": buildings_with_battery[:3]},
                "benefit": "기존 배터리 용량 5.0 증가로 에너지 저장 효율 향상"
            })
        
        # 5. 전력망 스마트 제어 시스템 (고급 옵션)
        # 전력망이 복잡해지면 추가 컨트롤 시스템 제안
        if len(city.lines) > 5 or len(city.buildings) > 10:
            upgrade_options.append({
                "id": "smart_grid",
                "text": "스마트 그리드 제어 시스템 도입",
                "cost": 120,
                "priority": 5,
                "category": "시스템",
                "target_data": {},
                "benefit": "AI 기반 전력 분배 최적화로 전체 송전망 효율 15% 향상"
            })
        
        # 6. 재난 대비 옵션 (높은 예산이 있을 때)
        if self.simulator.budget > 200:
            upgrade_options.append({
                "id": "disaster_prevention",
                "text": "전력망 재난 대비 시스템 구축",
                "cost": 150,
                "priority": 5,
                "category": "시스템",
                "target_data": {},
                "benefit": "자연재해 발생 시 정전 피해 50% 감소, 주요 인프라 전력 공급 보장"
            })
        
        # 우선순위와 예산에 따라 옵션 정렬 및 필터링
        # 최대 5개 옵션만 표시
        upgrade_options = sorted(upgrade_options, key=lambda x: (x['priority'], -x['cost']))[:5]
        
        # 버튼 생성
        current_y = button_start_y
        for i, option in enumerate(upgrade_options):
            # 옵션 텍스트 구성 (비용 포함)
            raw_button_text = f"{i+1}. {option['text']} (비용: {option['cost']})"
            if self.simulator.budget < option["cost"]:
                raw_button_text += " (예산 부족)"
            
            # 버튼 텍스트 길이 조절
            # 버튼 내부 패딩 등을 고려하여 실제 텍스트 영역 너비 계산 필요
            # 여기서는 버튼 너비의 90%를 최대 텍스트 너비로 가정합니다.
            button_text_max_width = button_width - 20 # 양쪽 여백 10px씩 고려
            button_text = raw_button_text
            if truncate_func:
                button_text = truncate_func(raw_button_text, current_font, button_text_max_width)
            else: # truncate_func 없는 경우 간단히 길이로 제한 (정확도 낮음)
                if len(raw_button_text) * (current_font.get_height() // 2) > button_text_max_width: # 대략적 계산
                    button_text = raw_button_text[:int(button_text_max_width / (current_font.get_height()//2))] + "..."

            # 버튼 생성
            rect = pygame.Rect(panel_x + 40, current_y, button_width, button_height)
            
            # 카테고리와 우선순위에 따라 버튼 색상 설정
            button_color = None
            if option['priority'] == 1:  # 최우선 - 빨간색 계열
                button_color = (230, 120, 120)
            elif option['category'] == '송전':
                button_color = (120, 180, 250)  # 파란색 계열
            elif option['category'] == '발전':
                button_color = (120, 230, 120)  # 녹색 계열
            elif option['category'] == '신재생':
                button_color = (230, 230, 120)  # 노란색 계열
            elif option['category'] == '저장':
                button_color = (200, 150, 230)  # 보라색 계열
            elif option['category'] == '시스템':
                button_color = (230, 170, 120)  # 주황색 계열
            
            # 콜백에 전달할 데이터 준비
            callback_data = {
                'id': option['id'],
                'cost': option['cost'],
                'target_data': option['target_data'],
                'benefit': option['benefit']
            }
            
            # 버튼 생성 및 저장
            button = Button(
                rect, 
                button_text,
                lambda opt=callback_data: self.handle_ai_option_select(opt),
                color=button_color
            )
            
            self.ai_upgrade_option_buttons.append(button)
            
            # 혜택 설명 텍스트 추가
            raw_benefit_text = f"   ↳ 효과: {option['benefit']}"""
            benefit_text_max_width = button_width - 40 # 버튼보다 조금 더 안쪽으로
            benefit_text = raw_benefit_text
            if truncate_func:
                benefit_text = truncate_func(raw_benefit_text, current_font, benefit_text_max_width) 
            else:
                if len(raw_benefit_text) * (current_font.get_height() // 2) > benefit_text_max_width:
                    benefit_text = raw_benefit_text[:int(benefit_text_max_width / (current_font.get_height()//2))] + "..."

            benefit_rect = pygame.Rect(panel_x + 60, current_y + button_height + 5, button_width - 20, 20) # Y 간격 5 추가
            
            # 혜택 텍스트용 특수 버튼(비활성화된) -> 색상을 밝게 조정 (예: (180, 180, 200))
            # Button 클래스에 text_color 인자가 있다면 (180,180,200) 같은 밝은 회색으로 지정하는 것이 더 좋음
            # 현재는 버튼 배경색을 밝게 하여 간접적으로 효과를 줌
            benefit_button_color = (210, 210, 230) # 매우 밝은 회색-파랑 계열 배경으로 변경
            benefit_button = Button(benefit_rect, benefit_text, lambda: None, color=benefit_button_color, active=False, text_color=(0, 0, 0)) # 텍스트 색상을 검은색으로 변경
            self.ai_upgrade_option_buttons.append(benefit_button)
            
            current_y += button_height + 20 + 5 + button_padding  # 버튼 + 혜택설명(높이20+간격5) + 패딩
        
        self.drawer.ai_upgrade_option_buttons = self.ai_upgrade_option_buttons
    
    def handle_ai_option_select(self, option_data):
        """AI 업그레이드 선택지 버튼 콜백 함수"""
        option_id = option_data['id']
        cost_of_selected_option = option_data['cost']
        target_data = option_data.get('target_data', {})
        
        # print(f"[DEBUG-UI] AI 업그레이드 옵션 선택됨: {option_id}, 현재 예산: {self.simulator.budget}")
        
        # 분석 결과 상태 확인
        analysis_output = getattr(self.drawer, 'current_grid_analysis_results', None)
        if analysis_output:
            problems = analysis_output.get('problems', [])
            # print(f"[DEBUG-UI] 현재 감지된 문제점 수: {len(problems)}")
            for p in problems:
                if p['type'] == 'overloaded_line':
                    # print(f"[DEBUG-UI] 과부하 송전선 문제: {p['description']}, 심각도: {p['severity']}")
                    pass
        
        if self.simulator.budget >= cost_of_selected_option:
            actual_spent_cost = 0
            
            try:
                if option_id == "upgrade_line":
                    # print(f"[DEBUG-UI] upgrade_critical_lines 함수 호출 시작...")
                    # target_data에서 특정 라인이 있으면 그 라인만 업그레이드
                    target_line = target_data.get('line')
                    if target_line:
                        self.simulator.target_line_for_upgrade = target_line
                    
                    actual_spent_cost = upgrade_critical_lines(self.simulator, cost_of_selected_option)
                    # print(f"[DEBUG-UI] upgrade_critical_lines 함수 반환 값: {actual_spent_cost}")
                    
                    # 업그레이드된 송전선 정보 확인 및 사용자에게 알림
                    if hasattr(self.simulator, 'last_upgraded_line') and self.simulator.last_upgraded_line:
                        line_info = self.simulator.last_upgraded_line
                        # print(f"[INFO] 송전선 {line_info['from']}-{line_info['to']} 용량 증설: {line_info['old_capacity']:.1f} → {line_info['new_capacity']:.1f} (사용률: {line_info['usage_rate']*100:.1f}%)")
                
                elif option_id == "upgrade_multiple_lines":
                    # 복수 송전선 업그레이드
                    # print(f"[DEBUG-UI] 다중 송전선 업그레이드 시작...")
                    lines = target_data.get('lines', [])
                    if lines:
                        per_line_budget = cost_of_selected_option / len(lines)
                        total_cost = 0
                        for line in lines:
                            self.simulator.target_line_for_upgrade = line
                            line_cost = upgrade_critical_lines(self.simulator, per_line_budget)
                            total_cost += line_cost
                        actual_spent_cost = total_cost
                        # print(f"[DEBUG-UI] 다중 송전선 업그레이드 완료, 총 비용: {actual_spent_cost:.1f}")
                
                elif option_id == "build_producer":
                    target_building = target_data.get('building')
                    if target_building:
                        self.simulator.target_building_for_producer = target_building
                    
                    actual_spent_cost = build_producer_in_needed_area(self.simulator, cost_of_selected_option)
                    # print(f"[DEBUG-UI] 발전소 건설 비용: {actual_spent_cost:.1f}")
                
                elif option_id == "add_solar" or option_id == "upgrade_solar":
                    # 태양광 설치 또는 업그레이드
                    buildings = target_data.get('buildings', [])
                    if buildings:
                        total_cost = 0
                        for building in buildings:
                            if option_id == "add_solar" and building.solar_capacity == 0:
                                building.solar_capacity = 5.0  # 신규 설치
                                total_cost += cost_of_selected_option / len(buildings)
                            elif option_id == "upgrade_solar" and building.solar_capacity > 0:
                                building.solar_capacity *= 1.5  # 50% 증가
                                total_cost += cost_of_selected_option / len(buildings)
                        
                        actual_spent_cost = total_cost
                        # print(f"[DEBUG-UI] 태양광 {option_id} 완료, 비용: {actual_spent_cost:.1f}")
                
                elif option_id == "add_battery" or option_id == "upgrade_battery":
                    # 배터리 설치 또는 업그레이드
                    buildings = target_data.get('buildings', [])
                    if option_id == "add_battery":
                        # 적절한 건물 선택 (발전소 또는 수요 큰 건물)
                        candidates = [b for b in self.simulator.city.buildings if not b.removed and (not hasattr(b, 'battery_capacity') or b.battery_capacity == 0)]
                        if candidates:
                            target_buildings = sorted(candidates, key=lambda b: abs(b.base_supply), reverse=True)[:3]
                            total_cost = 0
                            for building in target_buildings:
                                building.battery_capacity = 10.0
                                building.battery_charge = 5.0  # 절반 충전 상태로 시작
                                total_cost += cost_of_selected_option / len(target_buildings)
                            
                            actual_spent_cost = total_cost
                    else:  # upgrade_battery
                        if buildings:
                            total_cost = 0
                            for building in buildings:
                                if hasattr(building, 'battery_capacity') and building.battery_capacity > 0:
                                    building.battery_capacity += 5.0
                                    total_cost += cost_of_selected_option / len(buildings)
                            
                            actual_spent_cost = total_cost
                    
                    # print(f"[DEBUG-UI] 배터리 {option_id} 완료, 비용: {actual_spent_cost:.1f}")
                
                elif option_id == "smart_grid":
                    # 스마트 그리드 시스템 도입 - 모든 송전선 효율 향상
                    for line in self.simulator.city.lines:
                        if not line.removed:
                            # 용량 10% 증가
                            line.capacity *= 1.1
                            # 손실률 감소 등 추가 가능
                    
                    actual_spent_cost = cost_of_selected_option
                    # print(f"[DEBUG-UI] 스마트 그리드 시스템 도입 완료, 비용: {actual_spent_cost:.1f}")
                
                elif option_id == "disaster_prevention":
                    # 재난 대비 시스템 - 시뮬레이터에 플래그 설정
                    self.simulator.disaster_prevention_system = True
                    # 주요 인프라 건물 식별 및 강화 가능
                    
                    actual_spent_cost = cost_of_selected_option
                    # print(f"[DEBUG-UI] 재난 대비 시스템 구축 완료, 비용: {actual_spent_cost:.1f}")
                
            except Exception as e:
                # print(f"[ERROR] AI 업그레이드 실행 중 오류 발생: {str(e)}")
                import traceback
                traceback.print_exc()
            
            if actual_spent_cost > 0:
                self.simulator.budget -= actual_spent_cost
                # print(f"[DEBUG-UI] {option_id} 업그레이드에 {actual_spent_cost:.1f} 사용. 남은 예산: {self.simulator.budget:.1f}")
            elif actual_spent_cost == 0:
                # print(f"[DEBUG-UI] {option_id} 업그레이드가 실행되지 않았거나 비용이 발생하지 않음.")
                pass
        else:
            # print(f"[DEBUG-UI] 예산 부족 ({self.simulator.budget:.1f})으로 {option_id} 업그레이드 불가 (필요 예산: {cost_of_selected_option:.1f}).")
            pass

        # 업그레이드 시도 후에는 패널을 닫고 시뮬레이션 재개
        self.drawer.show_ai_upgrade_panel = False
        if hasattr(self.simulator, 'resume_simulation'):
            self.simulator.resume_simulation()
        self.ai_upgrade_option_buttons.clear() # 버튼 리스트 정리
        if hasattr(self.drawer, 'ai_upgrade_option_buttons'):
            self.drawer.ai_upgrade_option_buttons.clear()
        
        # 업그레이드 결과를 즉시 반영하기 위해 업데이트 
        # print("[DEBUG-UI] 시뮬레이터 update_flow 호출...")
        if hasattr(self.simulator, 'update_flow'):
            self.simulator.update_flow(instant=True)
            print("[DEBUG-UI] 시뮬레이터 update_flow 완료")
        else:
            print("[ERROR] 시뮬레이터에 update_flow 메서드가 없습니다.")
    
    def handle_events(self):
        """이벤트 처리"""
        mx, my = pygame.mouse.get_pos()
        wx, wy = self.drawer.screen_to_world(mx, my)
        
        # 마우스 오버 상태의 건물 및 라인 갱신 (툴팁 표시용)
        self.drawer.hover_bldg = self.pick_building(mx, my)
        self.drawer.hover_line = None
        if not self.drawer.hover_bldg:
            self.drawer.hover_line = self.pick_line(mx, my)
        
        # 이벤트 처리
        for event in pygame.event.get():
            # 컨텍스트 메뉴가 열려있는 경우 (메뉴가 존재하고 visible이 True인 경우만)
            if hasattr(self.drawer, 'context_menu') and hasattr(self.drawer.context_menu, 'visible') and self.drawer.context_menu.visible:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # 컨텍스트 메뉴 영역 클릭인지 확인
                    if hasattr(self.drawer.context_menu, 'x'):
                        menu_rect = pygame.Rect(self.drawer.context_menu.x, self.drawer.context_menu.y, 
                                               self.drawer.context_menu.width, self.drawer.context_menu.height)
                        if menu_rect.collidepoint(event.pos):
                            if self.drawer.context_menu.handle_click(event.pos):
                                continue
                        else:
                            # 메뉴 외부 클릭시 메뉴 닫기
                            self.drawer.context_menu.visible = False
            
            # AI 업그레이드 패널이 보여지고 있는 경우
            if hasattr(self.drawer, 'show_ai_upgrade_panel') and self.drawer.show_ai_upgrade_panel:
                if self.handle_ai_upgrade_panel_events(event, mx, my):
                    continue  # return 대신 continue로 변경하여 다른 이벤트도 처리 가능하게 함
            
            # 시나리오 목록이 보여지고 있는 경우
            if hasattr(self.drawer, 'show_scenario_list') and self.drawer.show_scenario_list:
                # 시나리오 패널 영역 계산
                scenario_panel_width = 400
                scenario_panel_height = 500
                scenario_panel_x = (self.drawer.width - scenario_panel_width) // 2
                scenario_panel_y = (self.drawer.height - scenario_panel_height) // 2
                scenario_panel_rect = pygame.Rect(scenario_panel_x, scenario_panel_y, scenario_panel_width, scenario_panel_height)
                
                if event.type == pygame.MOUSEBUTTONDOWN and scenario_panel_rect.collidepoint(mx, my):
                    if hasattr(self, 'handle_scenario_list_events'):
                        self.handle_scenario_list_events(event)
                    if hasattr(self, 'handle_scenario_list_ui') and self.handle_scenario_list_ui(event):
                        continue
            
            # 버튼 이벤트 처리
            for b in self.drawer.buttons:
                if hasattr(b, 'check_event'):  # Button 객체인 경우
                    b.check_event(event)
                elif isinstance(b, dict) and event.type == pygame.MOUSEBUTTONDOWN:  # dict 타입 버튼인 경우
                    button_rect = pygame.Rect(b['x'], b['y'], b['width'], b['height'])
                    if button_rect.collidepoint(mx, my) and 'action' in b:
                        b['action']()
            
            # 일반 이벤트 처리
            if event.type == pygame.QUIT:
                self.drawer.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key_event(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_down(event, mx, my, wx, wy)
            elif event.type == pygame.MOUSEBUTTONUP:
                self.handle_mouse_up(event)
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event)
    
    def handle_key_event(self, event):
        """키보드 이벤트 처리"""
        if event.key == pygame.K_ESCAPE:
            if self.drawer.add_mode == "waypoint" and self.drawer.editing_line:
                # waypoint 편집 취소
                self.drawer.editing_line = None
                self.drawer.temp_waypoints = []
                self.drawer.waypoint_mode = False
                self.drawer.add_mode = "none"
                print("waypoint 편집 취소")
            else:
                self.start_normal_mode()
        elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            if self.drawer.add_mode == "waypoint" and self.drawer.editing_line:
                # waypoint 편집 저장
                self.drawer.editing_line.waypoints = self.drawer.temp_waypoints.copy()
                print(f"송전선 {self.drawer.editing_line.u}-{self.drawer.editing_line.v}에 {len(self.drawer.editing_line.waypoints)}개 waypoint 저장")
                self.drawer.editing_line = None
                self.drawer.temp_waypoints = []
                self.drawer.waypoint_mode = False
                self.drawer.add_mode = "none"
                self.simulator.update_flow(instant=True)
        elif event.key == pygame.K_r:
            self.restore_all()
        elif event.key == pygame.K_F1:
            self.drawer.show_help = not self.drawer.show_help
    
    def handle_mouse_down(self, event, mx, my, wx, wy):
        """마우스 버튼 누름 이벤트 처리"""
        # UI 패널 영역 클릭은 무시
        if self.drawer.ui_rect.collidepoint(mx, my):
            return
        
        # 시나리오 목록이 열려있을 때 휠 스크롤 처리
        if self.drawer.show_scenario_list:
            # 시나리오 패널 영역 계산
            panel_width = 800
            panel_height = 800
            panel_x = (self.drawer.width - panel_width) // 2
            panel_y = 50
            panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
            
            # 시나리오 패널 영역 내에서 휠 이벤트는 스크롤로 처리
            if panel_rect.collidepoint(mx, my):
                if event.button == 4:  # 휠 업 (위로 스크롤)
                    self.drawer.scenario_scroll = max(self.drawer.scenario_scroll - 30, 0)
                    return
                elif event.button == 5:  # 휠 다운 (아래로 스크롤)
                    # 최대 스크롤 값 계산
                    item_h = 80
                    item_gap = 12
                    total_height = (item_h + item_gap) * len(self.simulator.scenarios)
                    visible_height = panel_height - 100
                    max_scroll = max(0, total_height - visible_height)
                    self.drawer.scenario_scroll = min(self.drawer.scenario_scroll + 30, max_scroll)
                    return
        
        # AI 업그레이드 패널이 열려있을 때도 휠 이벤트 처리
        if self.drawer.show_ai_upgrade_panel:
            panel_width = 800
            panel_height = 800
            panel_x = (self.drawer.width - panel_width) // 2
            panel_y = (self.drawer.height - panel_height) // 2
            panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
            
            # AI 패널 영역 내에서 휠 이벤트는 무시
            if panel_rect.collidepoint(mx, my):
                if event.button == 4 or event.button == 5:
                    return
        
        # 일반적인 휠 줌 아웃 처리
        if event.button == 4:  # 휠 업 (확대)
            self.drawer.zoom((mx, my), 1.1)
        elif event.button == 5:  # 휠 다운 (축소)
            self.drawer.zoom((mx, my), 1 / 1.1)
        elif event.button == 1:  # 왼쪽 버튼
            if self.drawer.add_mode == "waypoint":
                # waypoint 편집 모드
                if self.drawer.editing_line:
                    # 먼저 기존 waypoint를 클릭했는지 확인
                    nearest_waypoint_index = None
                    for i, (wp_x, wp_y) in enumerate(self.drawer.temp_waypoints):
                        dist = ((wx - wp_x) ** 2 + (wy - wp_y) ** 2) ** 0.5
                        if dist <= 20:  # 20픽셀 내
                            nearest_waypoint_index = i
                            break
                    
                    if nearest_waypoint_index is not None:
                        # 기존 waypoint 드래그 시작
                        self.drawer.dragging_waypoint = True
                        self.drawer.dragging_waypoint_index = nearest_waypoint_index
                        print(f"waypoint {nearest_waypoint_index} 드래그 시작")
                    else:
                        # 송전선 위의 점에 새로운 waypoint 추가
                        line = self.drawer.editing_line
                        u_pos = (self.simulator.city.buildings[line.u].x, self.simulator.city.buildings[line.u].y)
                        v_pos = (self.simulator.city.buildings[line.v].x, self.simulator.city.buildings[line.v].y)
                        
                        # PowerLine의 새로운 메서드를 사용하여 적절한 위치에 삽입
                        temp_line = PowerLine(line.u, line.v)
                        temp_line.waypoints = self.drawer.temp_waypoints.copy()
                        
                        if temp_line.insert_waypoint_on_line(wx, wy, u_pos, v_pos):
                            self.drawer.temp_waypoints = temp_line.waypoints.copy()
                            print(f"송전선 위에 waypoint 추가: ({wx:.1f}, {wy:.1f})")
                        else:
                            # 송전선 위가 아니면 끝에 추가
                            self.drawer.temp_waypoints.append((wx, wy))
                            print(f"waypoint 추가: ({wx:.1f}, {wy:.1f})")
            elif self.drawer.add_mode == "delete":
                # 삭제 모드에서는 건물이나 라인을 삭제
                delete_target_bldg = self.pick_building(mx, my)
                if delete_target_bldg:
                    delete_target_bldg.removed = True
                    self.simulator.update_flow(instant=True)
                else:
                    delete_target_line = self.pick_line(mx, my)
                    if delete_target_line:
                        delete_target_line.removed = True
                        self.simulator.update_flow(instant=True)
            elif self.drawer.add_mode == "select_line_for_waypoint":
                # waypoint 편집할 송전선 선택 모드
                print(f"[DEBUG] 송전선 선택 시도 중... mx={mx}, my={my}")
                selected_line = self.pick_line(mx, my)
                print(f"[DEBUG] pick_line 결과: {selected_line}")
                if selected_line:
                    # 송전선이 선택되면 waypoint 편집 모드 시작
                    self.drawer.editing_line = selected_line
                    self.drawer.temp_waypoints = selected_line.waypoints.copy()
                    self.drawer.waypoint_mode = True
                    self.drawer.add_mode = "waypoint"
                    print(f"송전선 {selected_line.u}-{selected_line.v} waypoint 편집 모드 시작")
                    print("사용법:")
                    print("  • 송전선 위 클릭: 해당 지점에 waypoint 추가")
                    print("  • waypoint 드래그: 위치 이동")
                    print("  • waypoint 우클릭: 해당 waypoint 삭제")
                    print("  • 빈 공간 우클릭: 마지막 waypoint 삭제")
                    print("  • Enter: 저장 및 완료")
                    print("  • ESC: 취소")
                else:
                    print("송전선을 클릭해주세요")
                    print(f"[DEBUG] 사용 가능한 송전선: {[(l.u, l.v) for l in self.simulator.city.lines if not l.removed]}")
            elif self.drawer.add_mode.startswith("add_"):
                if self.drawer.add_mode == "add_line":
                    # 송전선 추가 모드
                    self.handle_add_line(self.drawer.hover_bldg)
                else:
                    # 건물 추가 모드
                    self.handle_add_building(wx, wy)
            else:
                # 일반 모드에서는 드래그 시작
                if self.drawer.hover_bldg:
                    # 건물 드래그 시작
                    self.drawer.dragging_bldg = self.drawer.hover_bldg
                    self.drawer.drag_offset = (self.drawer.dragging_bldg.x - wx,
                                             self.drawer.dragging_bldg.y - wy)
                else:
                    # 배경 드래그 시작
                    self.drawer.dragging_background = True
                    self.drawer.drag_start = (mx, my)
                    self.drawer.old_offset = (self.drawer.offset_x, self.drawer.offset_y)
        elif event.button == 3:  # 오른쪽 버튼
            if self.drawer.add_mode == "waypoint" and self.drawer.editing_line:
                # waypoint 편집 모드에서 오른쪽 클릭
                # 먼저 클릭한 위치에 waypoint가 있는지 확인
                nearest_waypoint_index = None
                for i, (wp_x, wp_y) in enumerate(self.drawer.temp_waypoints):
                    dist = ((wx - wp_x) ** 2 + (wy - wp_y) ** 2) ** 0.5
                    if dist <= 20:  # 20픽셀 내
                        nearest_waypoint_index = i
                        break
                
                if nearest_waypoint_index is not None:
                    # 특정 waypoint 삭제
                    removed = self.drawer.temp_waypoints.pop(nearest_waypoint_index)
                    print(f"waypoint {nearest_waypoint_index} 삭제: ({removed[0]:.1f}, {removed[1]:.1f})")
                else:
                    # waypoint가 없는 곳을 오른클릭하면 마지막 waypoint 삭제 (기존 기능 유지)
                    if self.drawer.temp_waypoints:
                        removed = self.drawer.temp_waypoints.pop()
                        print(f"마지막 waypoint 삭제: ({removed[0]:.1f}, {removed[1]:.1f})")
            else:
                # 오른쪽 클릭으로 컨텍스트 메뉴 표시
                right_click_bldg = self.pick_building(mx, my)
                if right_click_bldg:
                    self.drawer.context_menu.show(mx, my, right_click_bldg)
                else:
                    right_click_line = self.pick_line(mx, my)
                    if right_click_line:
                        self.drawer.context_menu.show(mx, my, right_click_line)
    
    def handle_mouse_up(self, event):
        """마우스 버튼 놓음 이벤트 처리"""
        if event.button == 1:  # 왼쪽 버튼
            self.drawer.dragging_bldg = None
            self.drawer.dragging_background = False
            
            # waypoint 드래그 종료
            if self.drawer.dragging_waypoint:
                self.drawer.dragging_waypoint = False
                print(f"waypoint {self.drawer.dragging_waypoint_index} 드래그 완료")
                self.drawer.dragging_waypoint_index = -1
    
    def handle_mouse_motion(self, event):
        """마우스 움직임 이벤트 처리"""
        if self.drawer.dragging_waypoint:
            # waypoint 드래그 중
            if self.drawer.dragging_waypoint_index >= 0 and self.drawer.dragging_waypoint_index < len(self.drawer.temp_waypoints):
                cur_wx, cur_wy = self.drawer.screen_to_world(event.pos[0], event.pos[1])
                self.drawer.temp_waypoints[self.drawer.dragging_waypoint_index] = (cur_wx, cur_wy)
        elif self.drawer.dragging_bldg:
            # 건물 드래그 중
            cur_wx, cur_wy = self.drawer.screen_to_world(event.pos[0], event.pos[1])
            self.drawer.dragging_bldg.x = cur_wx + self.drawer.drag_offset[0]
            self.drawer.dragging_bldg.y = cur_wy + self.drawer.drag_offset[1]
            if self.drawer.force_layout_on_drag:
                self.building_repulsion(self.drawer.dragging_bldg)
        elif self.drawer.dragging_background:
            # 배경 드래그 중
            dx = event.pos[0] - self.drawer.drag_start[0]
            dy = event.pos[1] - self.drawer.drag_start[1]
            self.drawer.offset_x = self.drawer.old_offset[0] + dx
            self.drawer.offset_y = self.drawer.old_offset[1] + dy
    
    def handle_add_line(self, hover_bldg):
        """송전선 추가 처리"""
        # 송전선 추가 모드에서는 마우스 위치의 건물 찾기
        mx, my = pygame.mouse.get_pos()
        target_bldg = hover_bldg if hover_bldg else self.pick_building(mx, my)
        if target_bldg:
            if self.drawer.temp_line_start is None:
                # 시작 건물 설정
                self.drawer.temp_line_start = target_bldg
            else:
                # 끝 건물 설정 및 송전선 추가
                if target_bldg != self.drawer.temp_line_start:
                    self.simulator.city.add_line(
                        self.drawer.temp_line_start.idx,
                        target_bldg.idx,
                        5.0,
                        1.0
                    )
                    self.simulator.update_flow(instant=True)
                self.drawer.temp_line_start = None
    
    def handle_add_building(self, wx, wy):
        """건물 추가 처리"""
        if self.drawer.add_mode == "add_power_plant":
            # 발전소 추가 - 각 타입별 전용 함수 사용
            if self.selected_power_plant_type == "wind":
                self.simulator.city.add_wind_plant(
                    capacity=self.selected_power_capacity, x=wx, y=wy
                )
            elif self.selected_power_plant_type == "solar":
                self.simulator.city.add_solar_plant(
                    capacity=self.selected_power_capacity, x=wx, y=wy
                )
            elif self.selected_power_plant_type == "hydro":
                self.simulator.city.add_hydro_plant(
                    capacity=self.selected_power_capacity, x=wx, y=wy
                )
            elif self.selected_power_plant_type == "hydrogen":
                self.simulator.city.add_hydrogen_storage(
                    storage_capacity=self.selected_power_capacity, x=wx, y=wy
                )
            elif self.selected_power_plant_type == "nuclear":
                self.simulator.city.add_nuclear_plant(
                    capacity=self.selected_power_capacity, x=wx, y=wy
                )
            elif self.selected_power_plant_type == "thermal":
                self.simulator.city.add_thermal_plant(
                    capacity=self.selected_power_capacity, x=wx, y=wy
                )
        elif self.drawer.add_mode == "add_demand":
            sup = -5.0
            self.simulator.city.add_building(sup, wx, wy)
        elif self.drawer.add_mode == "add_shop":
            sup = -10.0  # 상가는 더 많은 전력 수요
            b = self.simulator.city.add_building(sup, wx, wy)
            b.building_type = "shopping_mall"
        elif self.drawer.add_mode == "add_junction":
            sup = 0.0  # 경유지는 전력 수요/공급이 없음
            self.simulator.city.add_building(sup, wx, wy)
        else:
            sup = 0.0
            self.simulator.city.add_building(sup, wx, wy)
        
        self.simulator.update_flow(instant=True)
        self.drawer.add_mode = "none"
        self.selected_power_plant_type = None
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    
    def handle_scenario_list_events(self, event):
        """시나리오 목록 스크롤 처리"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # 휠 업
                self.drawer.scenario_scroll = max(self.drawer.scenario_scroll - 30, 0)
            elif event.button == 5:  # 휠 다운
                self.drawer.scenario_scroll += 30
    
    def handle_scenario_list_ui(self, event):
        """시나리오 목록 UI 이벤트 처리"""
        w = 800
        h = 800
        left = (self.drawer.width - w) // 2
        top = 50
        panel_rect = pygame.Rect(left, top, w, h)
        
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            mx, my = event.pos
            if panel_rect.collidepoint(mx, my):
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    item_h = 80
                    item_gap = 12
                    ystart = top + 80 - self.drawer.scenario_scroll
                    
                    # 닫기 버튼 체크 (우상단 X 버튼)
                    close_btn = pygame.Rect(panel_rect.right - 40, panel_rect.top + 10, 30, 30)
                    if close_btn.collidepoint(mx, my):
                        self.drawer.show_scenario_list = False
                        return True
                    
                    for i, scen in enumerate(self.simulator.scenarios):
                        item_rect = pygame.Rect(left + 30, ystart, w - 60, item_h)
                        
                        # 화면에 보이는 영역만 체크
                        if item_rect.top > panel_rect.bottom:
                            break
                        if item_rect.bottom < panel_rect.top:
                            ystart += item_h + item_gap
                            continue
                            
                        if item_rect.collidepoint(mx, my):
                            # 전체 아이템 영역 클릭 시 시나리오 로드
                            print(f"시나리오 로드: {scen.get('name', '이름 없음')}")
                            self.simulator.load_scenario(scen)
                            self.drawer.show_scenario_list = False
                            return True
                        ystart += item_h + item_gap
                return True
        return False
    
    def pick_building(self, mx, my):
        """마우스 위치에 있는 건물 찾기"""
        thr = 20
        best = None
        distb = 999999
        wx, wy = self.drawer.screen_to_world(mx, my)
        for b in self.simulator.city.buildings:
            if b.removed:
                continue
            dx = b.x - wx
            dy = b.y - wy
            d = math.hypot(dx, dy)
            if d < thr and d < distb:
                distb = d
                best = b
        return best
    
    def pick_line(self, mx, my):
        """마우스 위치에 있는 송전선 찾기"""
        thr = 15
        best = None
        distb = 999999
        for pl in self.simulator.city.lines:
            if pl.removed:
                continue
            if self.simulator.city.buildings[pl.u].removed or self.simulator.city.buildings[pl.v].removed:
                continue
            x1 = self.simulator.city.buildings[pl.u].x
            y1 = self.simulator.city.buildings[pl.u].y
            x2 = self.simulator.city.buildings[pl.v].x
            y2 = self.simulator.city.buildings[pl.v].y
            sx1, sy1 = self.drawer.world_to_screen(x1, y1)
            sx2, sy2 = self.drawer.world_to_screen(x2, y2)
            d = point_line_dist(mx, my, sx1, sy1, sx2, sy2)
            if d < thr and d < distb:
                distb = d
                best = pl
        return best
    
    def building_repulsion(self, moved_b, radius=50):
        """건물 간 겹침 방지를 위한 반발력 적용"""
        for b in self.simulator.city.buildings:
            if b == moved_b or b.removed:
                continue
            dx = b.x - moved_b.x
            dy = b.y - moved_b.y
            dist = math.hypot(dx, dy)
            if dist < radius and dist > 1e-9:
                overlap = radius - dist
                push = overlap * 0.2
                angle = math.atan2(dy, dx)
                b.x += push * math.cos(angle)
                b.y += push * math.sin(angle)
                moved_b.x -= push * math.cos(angle)
                moved_b.y -= push * math.sin(angle)
    
    def handle_ai_upgrade_panel_events(self, event, mx, my):
        """AI 업그레이드 패널의 이벤트 처리"""
        # 패널 영역 계산
        panel_width = 800
        panel_height = 600
        panel_x = (self.drawer.width - panel_width) // 2
        panel_y = (self.drawer.height - panel_height) // 2
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.drawer.show_ai_upgrade_panel = False
            if hasattr(self.simulator, 'resume_simulation'):
                self.simulator.resume_simulation()
            else:
                print("[경고] Simulator에 resume_simulation 기능이 없어 수동으로 시간을 다시 시작해야 할 수 있습니다.")
            print("AI 업그레이드 패널을 닫습니다.")
            self.ai_upgrade_option_buttons.clear()
            if hasattr(self.drawer, 'ai_upgrade_option_buttons'):
                self.drawer.ai_upgrade_option_buttons.clear()
            return True

        # 마우스 클릭 시 버튼 이벤트 처리
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # 패널 영역 내부 클릭인 경우만 처리
            if panel_rect.collidepoint(mx, my):
                for button in self.ai_upgrade_option_buttons:
                    if button.rect.collidepoint(mx, my): # 마우스 클릭 위치와 버튼 충돌 검사
                        button.callback() # 버튼 콜백 실행
                        return True # 이벤트 처리됨
                return True  # 패널 내부 클릭은 처리됨으로 표시
            # 패널 외부 클릭은 false 반환하여 다른 UI 요소가 처리할 수 있게 함

        return False 