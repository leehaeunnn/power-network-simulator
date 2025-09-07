from datetime import datetime, timedelta
from modules.weather import WeatherSystem
from modules.power import PowerSystem
from modules.event import EventSystem
from city import CityGraph

class Simulator:
    def __init__(self):
        # 시뮬레이터 내부 상태
        self.city = CityGraph()
        
        # 시나리오 패턴 (ex: peak demand timeline 등)
        self.pattern = {
            "daily_pattern": [0.6,0.5,0.5,0.5,0.6,0.7,0.8,0.9,0.9,0.8,0.8,0.9,1.0,1.0,0.9,0.8,0.9,1.0,1.1,1.1,1.0,0.9,0.8,0.7],
            "weekly_pattern": [0.9,1.0,1.0,1.0,1.0,1.1,0.8], # 월~일
            "seasonal_pattern": [1.1,1.0,0.9,0.9,0.8,0.9,1.0,1.1,1.2,1.1,1.0,1.1], # 1월~12월
            "holiday_list": [{"month":1,"day":1},{"month":5,"day":5},{"month":8,"day":15},{"month":12,"day":25}], # 설, 어린이날, 광복절, 크리스마스 (예시)
            "holiday_factor": 1.2
        }
        
        # 예산, 자금, 이벤트 카운트
        self.budget = 1000.0
        self.event_count = 0
        
        # 시뮬레이션 시간
        self.simTime = datetime(2025,1,1,0,0,0)
        self.gameSpeed = 300.0  # 1초에 게임 시간 (분)
        
        # 하위 시스템 초기화
        self.weather_system = WeatherSystem(self)
        self.power_system = PowerSystem(self)
        self.event_system = EventSystem(self)
        
        # 경제 모델
        self.economic_model = None
        
        # 외부에서 불러올 시나리오 목록
        self.scenarios = []
        self.current_scenario = None
        self.current_scenario_index = -1
        self.action_log = []
        self.is_paused = False # 일시 정지 상태 변수 추가
    
    def pause_simulation(self):
        """시뮬레이션 일시 정지"""
        self.is_paused = True
        # print("[Simulator] 시뮬레이션 일시 정지됨")

    def resume_simulation(self):
        """시뮬레이션 재개"""
        self.is_paused = False
        # print("[Simulator] 시뮬레이션 재개됨")

    def set_economic_model(self, model):
        """경제 모델 설정"""
        self.economic_model = model
    
    def set_scenarios(self, scenarios):
        """
        외부에서 JSON을 읽은 뒤 시나리오 리스트를 넘겨받아 보관
        """
        self.scenarios = scenarios
    
    def load_scenario(self, scenario_data):
        # print(f"시나리오 로드 중: {scenario_data.get('name', '이름 없는 시나리오')}")
        self.city.clear_all()
        self.current_scenario = scenario_data

        # 예산을 scenario_data의 budget 또는 money 값으로 설정하되, 최소 1000.0 보장
        scenario_budget = scenario_data.get("budget", scenario_data.get("money", 1000.0))
        self.budget = max(float(scenario_budget), 1000.0)

        start_datetime_str = scenario_data.get("start_time", "2025-01-01 00:00:00")
        
        # 건물 재구성
        for binfo in scenario_data["buildings"]:
            # 발전소 타입에 따라 다른 메서드 호출
            building_type = binfo.get("building_type", "")
            
            if building_type == "wind_plant":
                b = self.city.add_wind_plant(
                    capacity=binfo.get("wind_capacity", 50.0),
                    x=binfo["x"], y=binfo["y"]
                )
            elif building_type == "solar_plant":
                b = self.city.add_solar_plant(
                    capacity=binfo.get("solar_capacity", 40.0),
                    x=binfo["x"], y=binfo["y"]
                )
            elif building_type == "hydro_plant":
                b = self.city.add_hydro_plant(
                    capacity=binfo.get("hydro_capacity", 60.0),
                    x=binfo["x"], y=binfo["y"]
                )
            elif building_type == "hydrogen_storage":
                b = self.city.add_hydrogen_storage(
                    storage_capacity=binfo.get("hydrogen_storage", 100.0),
                    x=binfo["x"], y=binfo["y"]
                )
            else:
                # 기존 건물 처리
                b = self.city.add_building(binfo["base_supply"], binfo["x"], binfo["y"])
                b.solar_capacity = binfo.get("solar_capacity", 0.0)
                b.wind_capacity = binfo.get("wind_capacity", 0.0)
                b.hydro_capacity = binfo.get("hydro_capacity", 0.0)
                b.hydrogen_storage = binfo.get("hydrogen_storage", 0.0)
                b.hydrogen_level = binfo.get("hydrogen_level", 0.0)
            
            # 공통 속성 설정
            if "name" in binfo:
                b.name = binfo["name"]
            b.removed = binfo.get("removed", False)
            b.is_prosumer = binfo.get("is_prosumer", False)
            b.building_type = binfo.get("building_type", "apartment")
            b.heating_source = binfo.get("heating_source", "electric")
            b.heating_type = binfo.get("heating_type", "electric")
            b.heating_cop = binfo.get("heating_cop", 1.0)
            b.humidity_sensitivity = binfo.get("humidity_sensitivity", 1.0)
            b.panel_tilt = binfo.get("panel_tilt", 30)
            b.panel_azimuth = binfo.get("panel_azimuth", 180)
            b.battery_capacity = binfo.get("battery_capacity", 0.0)
            b.battery_charge = binfo.get("battery_charge", 0.0)
            b.smart_grid_connected = binfo.get("smart_grid_connected", False)
            b.energy_efficiency = binfo.get("energy_efficiency", 1.0)
        
        # 송전선 재구성
        for linfo in scenario_data["lines"]:
            pl = self.city.add_line(linfo["u"], linfo["v"], linfo["capacity"], linfo["cost"])
            if pl is not None:
                pl.removed = linfo.get("removed", False)
        
        # 날씨 한번 업데이트
        self.weather_system.update_weather()
        
        # 전력 흐름 초기 계산
        self.update_flow(instant=True)
    
    def get_current_season(self):
        month = self.simTime.month
        if 3 <= month <= 5:
            return "봄"
        elif 6 <= month <= 8:
            return "여름"
        elif 9 <= month <= 11:
            return "가을"
        else:
            return "겨울"
    
    def apply_demand_pattern(self, region="Seoul"):
        """수요 패턴 적용 - Power 시스템으로 위임"""
        self.power_system.apply_demand_pattern(region)
    
    def calc_total_flow(self):
        """총 전력 흐름 계산 - 실제 공급량 반환"""
        return self.power_system.calc_total_flow()
    
    def update_flow(self, instant=False):
        """전력 흐름 업데이트"""
        self.power_system.update_flow(instant)
    
    def update_sim_time(self, dt_ms):
        """시뮬레이션 시간 업데이트"""
        if self.is_paused: # 일시 정지 상태면 시간 업데이트 안 함
            return

        dt_sec = dt_ms / 1000.0
        dt_simulated = dt_sec * self.gameSpeed
        self.simTime = self.simTime + timedelta(seconds=dt_simulated)
        
        # 날씨 시스템 업데이트
        self.weather_system.update(dt_ms)
        
        # 배터리 업데이트
        if self.economic_model:
            self.economic_model.update_energy_prices(dt_ms)
        
        self.power_system.update_battery()
    
    def update_events(self):
        """이벤트 업데이트"""
        self.event_system.update_events()
    
    def get_simulation_stats(self):
        """시뮬레이션 통계 데이터 수집"""
        stats = {
            "total_demand": abs(self.city.total_demand()),
            "total_supply": sum(b.current_supply for b in self.city.buildings if b.current_supply > 0 and not b.removed),
            "total_flow": self.calc_total_flow(),
            "blackout_buildings": len([b for b in self.city.buildings if b.blackout]),
            "solar_capacity": sum(b.solar_capacity for b in self.city.buildings if not b.removed),
            "battery_capacity": sum(b.battery_capacity for b in self.city.buildings if not b.removed),
            "battery_charge": sum(b.battery_charge for b in self.city.buildings if not b.removed),
            "budget": self.budget,
            "event_count": self.event_count,
            "current_weather": self.weather_system.current_weather,
            "current_temperature": self.weather_system.current_temperature
        }
        
        # 경제 모델이 있으면 경제 지표 추가
        if self.economic_model:
            econ_stats = self.economic_model.get_economic_stats()
            stats.update(econ_stats)
            
        return stats 