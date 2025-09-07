class Building:
    def __init__(self, idx, base_supply=0.0):
        self.idx=idx
        self.base_supply=base_supply  # 기본 공급량 (음수=수요)
        self.solar_capacity=0.0       # 태양광 설치 용량
        self.wind_capacity=0.0        # 풍력 발전 용량
        self.hydro_capacity=0.0       # 수력 발전 용량
        self.hydrogen_storage=0.0     # 그린수소 저장 용량
        self.hydrogen_level=0.0       # 현재 수소 저장량
        self.hydrogen_efficiency=0.6  # 수소 변환 효율 (60%)
        self.current_supply=base_supply
        self.x=0
        self.y=0
        self.removed=False
        self.blackout=False
        self.is_prosumer=False        # 프로슈머 여부
        self.power_plant_type=None    # 발전소 타입 (wind, solar, hydro, hydrogen, thermal)
        
        # 발전소별 세부 속성
        self.efficiency=1.0           # 발전 효율
        self.maintenance_cost=0.0     # 유지보수 비용
        self.carbon_emission=0.0      # 탄소 배출량
        self.weather_dependency=0.0   # 날씨 의존도 (0~1)
        
        # 수소 저장소 추가 속성
        self.hydrogen_production_rate=0.0  # 수소 생산률 (MW당 kg/h)
        self.hydrogen_consumption_rate=0.0 # 수소 소비률 (kg당 MW)
        self.electrolysis_efficiency=0.75  # 전기분해 효율 (75%)
        self.fuel_cell_efficiency=0.55     # 연료전지 효율 (55%)

    def get_type_str(self):
        # building_type 속성이 있으면 우선적으로 사용
        if hasattr(self, 'building_type') and self.building_type:
            type_mapping = {
                "shopping_mall": "상가",
                "apartment": "아파트",
                "factory": "공장",
                "office": "사무실",
                "hospital": "병원",
                "school": "학교",
                "hydrogen_storage": "수소저장소"
            }
            if self.building_type in type_mapping:
                return type_mapping[self.building_type]
        
        # power_plant_type이 있으면 발전소 타입 반환
        if self.power_plant_type:
            type_names = {
                "wind": "풍력발전소",
                "solar": "태양광발전소",
                "hydro": "수력발전소",
                "hydrogen": "수소발전소",
                "thermal": "화력발전소"
            }
            return type_names.get(self.power_plant_type, "발전소")
        elif self.base_supply > 0:
            return "발전소"
        elif self.solar_capacity > 0:
            if self.is_prosumer:
                return "프로슈머"
            elif self.base_supply < 0:
                return "태양광아파트"
            else:
                return "태양광상가"
        elif self.base_supply < 0:
            return "아파트"
        else:
            return "상가"

    def get_status_str(self):
        status = []
        if self.base_supply != 0:
            status.append(f"기본: {self.base_supply:+.1f}")
        if self.solar_capacity > 0:
            status.append(f"태양광: {self.solar_capacity:+.1f}")
        if self.wind_capacity > 0:
            status.append(f"풍력: {self.wind_capacity:+.1f}")
        if self.hydro_capacity > 0:
            status.append(f"수력: {self.hydro_capacity:+.1f}")
        if self.hydrogen_storage > 0:
            status.append(f"수소저장: {self.hydrogen_level:.1f}/{self.hydrogen_storage:.1f}")
        if self.current_supply != self.base_supply:
            status.append(f"현재: {self.current_supply:+.1f}")
        if self.blackout:
            status.append("정전!")
        return ", ".join(status)

# 풍력발전소 클래스
class WindPowerPlant(Building):
    def __init__(self, idx, capacity=100.0):
        super().__init__(idx, base_supply=0)  # 풍력은 base_supply 없음
        self.power_plant_type = "wind"
        self.wind_capacity = capacity
        self.efficiency = 0.35  # 풍력 발전 효율 35%
        self.maintenance_cost = 0.02  # 유지보수 비용 (용량 대비 2%)
        self.carbon_emission = 0.0  # 탄소 배출 없음
        self.weather_dependency = 1.0  # 날씨 의존도 100%
        self.rated_wind_speed = 12.0  # 정격 풍속 (m/s)
        self.cut_in_speed = 3.0  # 시동 풍속
        self.cut_out_speed = 25.0  # 정지 풍속
        
    def calculate_output(self, wind_speed):
        """풍속에 따른 발전량 계산"""
        if wind_speed < self.cut_in_speed or wind_speed > self.cut_out_speed:
            return 0
        elif wind_speed <= self.rated_wind_speed:
            # 큐빅 곡선으로 발전량 증가
            return self.wind_capacity * (wind_speed / self.rated_wind_speed) ** 3
        else:
            # 정격 풍속 이상에서는 일정한 출력
            return self.wind_capacity

# 태양광발전소 클래스  
class SolarPowerPlant(Building):
    def __init__(self, idx, capacity=80.0):
        super().__init__(idx, base_supply=0)
        self.power_plant_type = "solar"
        self.solar_capacity = capacity
        self.efficiency = 0.20  # 태양광 패널 효율 20%
        self.maintenance_cost = 0.01  # 유지보수 비용 (용량 대비 1%)
        self.carbon_emission = 0.0  # 탄소 배출 없음
        self.weather_dependency = 0.8  # 날씨 의존도 80%
        self.panel_tilt = 35  # 패널 경사각
        self.panel_azimuth = 180  # 패널 방위각 (남향)
        self.temperature_coefficient = -0.004  # 온도계수 (-0.4%/°C)
        
    def calculate_output(self, solar_radiation, temperature=25):
        """일사량과 온도에 따른 발전량 계산"""
        # 온도 보정 (25°C 기준)
        temp_factor = 1 + self.temperature_coefficient * (temperature - 25)
        return self.solar_capacity * solar_radiation * temp_factor * self.efficiency

# 수력발전소 클래스
class HydroPowerPlant(Building):
    def __init__(self, idx, capacity=150.0):
        super().__init__(idx, base_supply=capacity)
        self.power_plant_type = "hydro"
        self.hydro_capacity = capacity
        self.efficiency = 0.90  # 수력 발전 효율 90%
        self.maintenance_cost = 0.015  # 유지보수 비용 (용량 대비 1.5%)
        self.carbon_emission = 0.0  # 탄소 배출 없음
        self.weather_dependency = 0.3  # 날씨 의존도 30% (계절 영향)
        self.water_flow_rate = 100  # 기준 유량 (m³/s)
        self.head_height = 50  # 낙차 (m)
        self.turbine_efficiency = 0.85  # 터빈 효율
        
    def calculate_output(self, water_level_factor=1.0):
        """수위에 따른 발전량 계산"""
        # 계절별 수위 변동 반영
        return self.hydro_capacity * water_level_factor * self.efficiency

# 수소 에너지 저장소 클래스
class HydrogenEnergyStorage(Building):
    def __init__(self, idx, storage_capacity=1000.0):
        super().__init__(idx, base_supply=0)
        self.power_plant_type = "hydrogen"
        self.hydrogen_storage = storage_capacity  # 수소 저장 용량 (kg)
        self.hydrogen_level = 0.0  # 현재 저장량 (kg)
        
        # 수소 시스템 효율
        self.electrolysis_efficiency = 0.75  # 전기분해 효율 75%
        self.fuel_cell_efficiency = 0.55  # 연료전지 효율 55%
        self.round_trip_efficiency = 0.41  # 왕복 효율 (0.75 * 0.55)
        
        # 운영 파라미터
        self.max_charge_rate = 50.0  # 최대 충전 속도 (MW)
        self.max_discharge_rate = 50.0  # 최대 방전 속도 (MW)
        self.hydrogen_energy_density = 33.33  # kWh/kg (LHV 기준)
        
        # 비용 및 환경
        self.maintenance_cost = 0.025  # 유지보수 비용 (용량 대비 2.5%)
        self.carbon_emission = 0.0  # 그린수소는 탄소 배출 없음
        self.weather_dependency = 0.0  # 날씨 의존도 없음
        
    def charge(self, power_input, duration=1.0):
        """잉여 전력으로 수소 생산 (전기분해)"""
        if power_input <= 0 or self.hydrogen_level >= self.hydrogen_storage:
            return 0
            
        # 충전 가능한 전력량 제한
        effective_power = min(power_input, self.max_charge_rate)
        
        # 전력을 수소로 변환 (kWh -> kg)
        hydrogen_produced = (effective_power * duration * self.electrolysis_efficiency) / self.hydrogen_energy_density
        
        # 저장 가능량 확인
        storage_available = self.hydrogen_storage - self.hydrogen_level
        actual_stored = min(hydrogen_produced, storage_available)
        
        self.hydrogen_level += actual_stored
        
        # 실제 소비된 전력량 반환
        power_consumed = (actual_stored * self.hydrogen_energy_density) / self.electrolysis_efficiency / duration
        return power_consumed
        
    def discharge(self, power_demand, duration=1.0):
        """수소를 전력으로 변환 (연료전지)"""
        if power_demand <= 0 or self.hydrogen_level <= 0:
            return 0
            
        # 방전 가능한 전력량 제한
        effective_demand = min(power_demand, self.max_discharge_rate)
        
        # 필요한 수소량 계산 (kWh -> kg)
        hydrogen_needed = (effective_demand * duration) / (self.hydrogen_energy_density * self.fuel_cell_efficiency)
        
        # 사용 가능량 확인
        actual_used = min(hydrogen_needed, self.hydrogen_level)
        
        self.hydrogen_level -= actual_used
        
        # 실제 생산된 전력량 반환
        power_generated = (actual_used * self.hydrogen_energy_density * self.fuel_cell_efficiency) / duration
        return power_generated
        
    def get_storage_percentage(self):
        """저장률 반환 (%)"""
        if self.hydrogen_storage > 0:
            return (self.hydrogen_level / self.hydrogen_storage) * 100
        return 0

class PowerLine:
    def __init__(self, u,v,capacity=5.0,cost=1.0):
        self.u=u
        self.v=v
        self.capacity=capacity
        self.cost=cost
        self.flow=0.0
        self.removed=False

class CityGraph:
    def __init__(self):
        self.buildings=[]
        self.lines=[]
        self.n=0

    def add_building(self, base_supply=0.0,x=0,y=0):
        b=Building(self.n,base_supply)
        b.x,b.y=x,y
        if base_supply == 0:  # 상가인 경우
            b.base_supply = -2.0  # 기본 전력 소비를 -2.0으로 설정
        self.buildings.append(b)
        self.n+=1
        return b

    def add_line(self,u,v,cap=5.0,cost=1.0):
        pl=PowerLine(u,v,cap,cost)
        self.lines.append(pl)
    
    def add_wind_plant(self, capacity=50.0, x=0, y=0):
        """풍력발전소 추가"""
        b = Building(self.n, 0)
        b.x, b.y = x, y
        b.wind_capacity = capacity
        b.base_supply = 0  # 풍력은 날씨에 따라 변동
        b.power_plant_type = "wind"
        self.buildings.append(b)
        self.n += 1
        return b
    
    def add_solar_plant(self, capacity=40.0, x=0, y=0):
        """태양광발전소 추가"""
        b = Building(self.n, 0)
        b.x, b.y = x, y
        b.solar_capacity = capacity
        b.base_supply = 0  # 태양광은 일조량에 따라 변동
        b.power_plant_type = "solar"
        self.buildings.append(b)
        self.n += 1
        return b
    
    def add_hydro_plant(self, capacity=60.0, x=0, y=0):
        """수력발전소 추가"""
        b = Building(self.n, capacity)
        b.x, b.y = x, y
        b.hydro_capacity = capacity
        b.base_supply = capacity * 0.8  # 수력은 안정적, 80% 기본 발전
        b.power_plant_type = "hydro"
        self.buildings.append(b)
        self.n += 1
        return b
    
    def add_hydrogen_storage(self, storage_capacity=100.0, x=0, y=0):
        """그린수소 에너지 저장소 추가"""
        b = Building(self.n, 0)
        b.x, b.y = x, y
        b.hydrogen_storage = storage_capacity
        b.hydrogen_level = 0
        b.power_plant_type = "hydrogen"
        self.buildings.append(b)
        self.n += 1
        return b

    def total_demand(self):
        return sum(-b.current_supply for b in self.buildings if b.current_supply<0 and not b.removed)

    def build_capacity(self, buildings=None, power_lines=None):
        """네트워크 흐름을 위한 용량 그래프 구성
        
        Returns:
            (graph, source, sink) 튜플:
            - graph: {u: {v: capacity}} 형태의 용량 그래프
            - source: 슈퍼소스 노드 번호
            - sink: 슈퍼싱크 노드 번호
        """
        print("[build_capacity] 호출됨 - 그래프 용량 구성 시작 --------------------------------")
        
        # 외부에서 전달된 buildings와 power_lines가 있으면 사용
        buildings = buildings if buildings is not None else self.buildings
        power_lines = power_lines if power_lines is not None else self.lines
        
        # 노드 수 계산 (buildings 길이 + 슈퍼소스/싱크)
        self.n = len(buildings)
        S_star = self.n        # 슈퍼소스
        T_star = self.n + 1    # 슈퍼싱크
        
        # 그래프를 딕셔너리로 초기화
        self.graph = {}
        self.source = S_star
        self.sink = T_star

        print("  [build_capacity] 송전선(capacity) 설정 중...")
        for pl in power_lines:
            if pl.removed:
                continue
            if buildings[pl.u].removed or buildings[pl.v].removed:
                continue
            if pl.capacity > 1e-9:
                # 정방향 용량 설정
                if pl.u not in self.graph:
                    self.graph[pl.u] = {}
                self.graph[pl.u][pl.v] = pl.capacity
                
                # 역방향 용량 초기화 (0으로)
                if pl.v not in self.graph:
                    self.graph[pl.v] = {}
                self.graph[pl.v][pl.u] = 0
                
                print(f"    선({pl.u}->{pl.v}), capacity={pl.capacity:.2f}")

        print("  [build_capacity] 발전소/수요지 연결 설정 중...")
        # 슈퍼소스/싱크 노드 초기화
        self.graph[S_star] = {}
        self.graph[T_star] = {}
        
        for b in buildings:
            if b.removed:
                continue
            idx = b.idx
            
            # 노드 초기화
            if idx not in self.graph:
                self.graph[idx] = {}
            
            # 공급 건물
            if b.current_supply > 1e-9:
                self.graph[S_star][idx] = b.current_supply
                self.graph[idx][S_star] = 0  # 역방향
                print(f"    슈퍼소스 -> {idx}, supply={b.current_supply:.2f}")

            # 수요 건물(음수)
            elif b.current_supply < -1e-9:
                demand_val = -b.current_supply
                self.graph[idx][T_star] = demand_val
                self.graph[T_star][idx] = 0  # 역방향
                print(f"    {idx} -> 슈퍼싱크, demand={demand_val:.2f}")

        print("[build_capacity] 그래프 용량 구성 완료 -----------------------------------------\n")
        return self.graph, S_star, T_star

    def restore_all(self):
        for b in self.buildings:
            b.removed=False
        for pl in self.lines:
            pl.removed=False 