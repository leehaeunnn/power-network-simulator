class Building:
    def __init__(self, idx, base_supply=0.0, name=None):
        self.idx=idx
        self.name = name if name else f"건물_{idx}" # 이름 속성 추가
        self.base_supply=base_supply  # 기본 공급량 (음수=수요)
        self.solar_capacity=0.0       # 태양광 설치 용량
        self.current_supply=base_supply
        self.transmitted_power=0.0    # 실제 송전량 추적
        self.x=0
        self.y=0
        self.removed=False
        self.blackout=False
        self.is_prosumer=False        # 프로슈머 여부
        
        # 추가 속성들
        self.building_type = "apartment"    # 건물 유형: apartment, office, school, hospital, shopping_mall
        self.energy_efficiency = 1.0        # 에너지 효율 (1.0 = 기본, 낮을수록 효율 높음)
        self.year_built = 2010              # 건설 연도
        self.area = 1000                    # 건물 면적 (제곱미터)
        self.heating_source = "electric"    # 난방 방식: electric, gas, district
        self.heating_type = "electric"      # 난방 유형: electric, heat_pump, gas
        self.heating_cop = 1.0              # 난방 COP (히트펌프 용)
        self.humidity_sensitivity = 1.0     # 습도에 대한 민감도
        self.panel_tilt = 30                # 태양광 패널 경사각 (도)
        self.panel_azimuth = 180            # 태양광 패널 방위각 (도, 남쪽=180)
        self.smart_grid_connected = False   # 스마트 그리드 연결 여부
        self.battery_capacity = 0.0         # 배터리 저장 용량
        self.battery_charge = 0.0           # 현재 배터리 충전량
        self.shortage = 0.0                 # 현재 부족 전력량 (check_blackouts에서 계산)
        
        # 재생에너지 발전소 속성
        self.wind_capacity = 0.0            # 풍력 발전 용량
        self.hydro_capacity = 0.0           # 수력 발전 용량
        self.hydrogen_storage = 0.0         # 그린수소 저장 용량
        self.hydrogen_level = 0.0           # 현재 수소 저장량
        self.hydrogen_efficiency = 0.6      # 수소 변환 효율 (60%)
        self.power_plant_type = None        # 발전소 타입 (wind, solar, hydro, hydrogen, thermal)

    def get_type_str(self):
        # building_type이 명시적으로 설정되어 있으면 우선 사용
        if self.building_type == "shopping_mall":
            return "상가"
        elif self.building_type == "apartment":
            return "아파트"
        elif self.building_type == "office":
            return "사무실"
        elif self.building_type == "school":
            return "학교"
        elif self.building_type == "hospital":
            return "병원"
        elif self.building_type == "factory":
            return "공장"
        
        # 발전소 유형 확인 
        if self.power_plant_type:
            type_names = {
                "wind": "풍력발전소",
                "solar": "태양광발전소", 
                "hydro": "수력발전소",
                "hydrogen": "수소저장소",
                "nuclear": "원자력발전소",
                "thermal": "화력발전소"
            }
            return type_names.get(self.power_plant_type, "발전소")
        
        if self.base_supply > 0: # 발전소
            return "발전소"
        
        if self.is_prosumer: # 프로슈머
            return "프로슈머"

        if self.solar_capacity > 0: # 태양광 시설이 있고 프로슈머가 아닌 경우
            if self.base_supply < 0: # 태양광 + 수요 (예: 태양광 아파트)
                return "태양광아파트"
            else: # 태양광만
                return "태양광발전"

        if self.base_supply < 0: # 순수 수요 건물
            return "아파트"
            
        # base_supply == 0, solar_capacity == 0, is_prosumer == False
        return "중립시설"

    def get_status_str(self):
        status = []
        if self.base_supply > 0:  # 발전소인 경우
            status.append(f"발전: {self.base_supply:+.1f}")
            status.append(f"출력: {self.transmitted_power:+.1f}")
        elif self.base_supply != 0:
            status.append(f"기본: {self.base_supply:+.1f}")
            
            # 추가 정보: 에너지 효율
            efficiency_str = "상" if self.energy_efficiency < 0.8 else "중" if self.energy_efficiency < 1.2 else "하"
            status.append(f"효율: {efficiency_str}")
            
        if self.solar_capacity > 0:
            status.append(f"태양광: {self.solar_capacity:+.1f}")
            status.append(f"각도: {self.panel_tilt}°")
        
        if self.current_supply != self.base_supply:
            status.append(f"현재: {self.current_supply:+.1f}")
        
        if self.battery_capacity > 0:
            charge_percent = (self.battery_charge / self.battery_capacity) * 100
            status.append(f"배터리: {charge_percent:.0f}%")
            
        if self.blackout:
            status.append("정전!")
            
        # 난방 정보 표시
        if self.heating_source != "electric":
            status.append(f"난방: {self.heating_source}")
            
        # 스마트 그리드 연결 정보
        if self.smart_grid_connected:
            status.append("스마트그리드")
            
        return ", ".join(status)
        
    def get_detailed_info(self):
        """
        건물에 대한 상세 정보를 반환 (툴팁 표시용)
        """
        info = []
        info.append(f"ID: {self.idx}")
        info.append(f"유형: {self.get_type_str()}")
        
        if self.base_supply > 0:  # 발전소
            info.append(f"기본 발전량: {self.base_supply:.1f}")
            info.append(f"현재 발전량: {self.current_supply:.1f}")
            info.append(f"실제 송전량: {self.transmitted_power:.1f}")
        else:
            info.append(f"기본 수요: {-self.base_supply:.1f}")
            info.append(f"현재 수요: {-self.current_supply:.1f}")
            
        if self.solar_capacity > 0:
            info.append(f"태양광 용량: {self.solar_capacity:.1f}")
            info.append(f"패널 경사각: {self.panel_tilt}°")
            info.append(f"패널 방위각: {self.panel_azimuth}°")
            
        info.append(f"건설 연도: {self.year_built}")
        info.append(f"건물 면적: {self.area}㎡")
        
        if self.heating_source != "electric":
            info.append(f"난방 방식: {self.heating_source}")
            
        if self.heating_type == "heat_pump":
            info.append(f"난방 COP: {self.heating_cop:.1f}")
            
        if self.battery_capacity > 0:
            info.append(f"배터리 용량: {self.battery_capacity:.1f}")
            info.append(f"현재 충전량: {self.battery_charge:.1f} ({(self.battery_charge/self.battery_capacity)*100:.0f}%)")
            
        if self.smart_grid_connected:
            info.append("스마트 그리드 연결됨")
            
        if self.blackout:
            info.append("⚠️ 정전 상태")
            
        return info

class PowerLine:
    def __init__(self, u,v,capacity=5.0,cost=1.0):
        self.u=u
        self.v=v
        self.capacity=capacity
        self.waypoints = []  # 경유점 리스트 [(x1,y1), (x2,y2), ...]
        self.cost=cost
        self.flow=0.0
        self.removed=False
        self.usage_rate=0.0  # 사용률
    
    def add_waypoint(self, x, y, index=None):
        """경유점 추가 (index가 None이면 끝에 추가)"""
        if index is None:
            self.waypoints.append((x, y))
        else:
            self.waypoints.insert(index, (x, y))
    
    def remove_waypoint(self, index):
        """특정 인덱스의 경유점 제거"""
        if 0 <= index < len(self.waypoints):
            del self.waypoints[index]
    
    def move_waypoint(self, index, x, y):
        """특정 인덱스의 경유점 위치 변경"""
        if 0 <= index < len(self.waypoints):
            self.waypoints[index] = (x, y)
    
    def find_nearest_waypoint(self, x, y, max_distance=20):
        """가장 가까운 경유점의 인덱스를 반환 (최대 거리 내)"""
        min_distance = float('inf')
        nearest_index = -1
        
        for i, (wx, wy) in enumerate(self.waypoints):
            distance = ((x - wx) ** 2 + (y - wy) ** 2) ** 0.5
            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                nearest_index = i
        
        return nearest_index if nearest_index != -1 else None
    
    def insert_waypoint_on_line(self, x, y, u_pos, v_pos, max_distance=10):
        """송전선 위의 한 점에 새로운 경유점 삽입"""
        if not self.waypoints:
            # 경유점이 없으면 직선상에서 가장 가까운 점 찾기
            if self._point_on_line_segment(x, y, u_pos[0], u_pos[1], v_pos[0], v_pos[1], max_distance):
                self.waypoints.append((x, y))
                return True
        else:
            # 기존 경유점들 사이의 선분에서 삽입할 위치 찾기
            all_points = [u_pos] + self.waypoints + [v_pos]
            
            for i in range(len(all_points) - 1):
                p1 = all_points[i]
                p2 = all_points[i + 1]
                
                if self._point_on_line_segment(x, y, p1[0], p1[1], p2[0], p2[1], max_distance):
                    # i번째 선분에 삽입 (waypoints 인덱스로는 i)
                    self.waypoints.insert(i, (x, y))
                    return True
        
        return False
    
    def _point_on_line_segment(self, px, py, x1, y1, x2, y2, max_distance):
        """점이 선분 위에 있는지 확인 (최대 거리 내)"""
        # 선분의 길이
        line_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        if line_length == 0:
            return False
        
        # 점에서 선분으로의 최단거리 계산
        t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_length ** 2)))
        closest_x = x1 + t * (x2 - x1)
        closest_y = y1 + t * (y2 - y1)
        
        distance = ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5
        return distance <= max_distance
    
    def clear_waypoints(self):
        """모든 경유점 제거"""
        self.waypoints = []

class CityGraph:
    def __init__(self):
        self.buildings=[]
        self.lines=[]
        self.n=0

    def clear_all(self):
        """모든 건물과 송전선을 제거하고 초기화합니다."""
        self.buildings = []
        self.lines = []
        self.n = 0
        print("[CityGraph] 모든 데이터가 초기화되었습니다.")

    def add_building(self, base_supply=0.0, x=0, y=0, building_type="apartment", name=None, 
                     solar_capacity=0.0, is_prosumer=False, power_plant_type=None,
                     wind_capacity=0.0, hydro_capacity=0.0, hydrogen_storage=0.0):
        """건물 또는 발전소 추가"""
        from models import Building, WindPowerPlant, SolarPowerPlant, HydroPowerPlant, HydrogenEnergyStorage
        
        # 발전소 타입에 따라 적절한 객체 생성
        if power_plant_type == "wind":
            b = WindPowerPlant(self.n, capacity=wind_capacity if wind_capacity > 0 else 100.0)
            actual_name = name if name else f"풍력발전소_{self.n}"
        elif power_plant_type == "solar":
            b = SolarPowerPlant(self.n, capacity=solar_capacity if solar_capacity > 0 else 80.0)
            actual_name = name if name else f"태양광발전소_{self.n}"
        elif power_plant_type == "hydro":
            b = HydroPowerPlant(self.n, capacity=hydro_capacity if hydro_capacity > 0 else 150.0)
            actual_name = name if name else f"수력발전소_{self.n}"
        elif power_plant_type == "hydrogen":
            b = HydrogenEnergyStorage(self.n, storage_capacity=hydrogen_storage if hydrogen_storage > 0 else 1000.0)
            actual_name = name if name else f"수소저장소_{self.n}"
        else:
            # 기존 건물 생성 로직
            b = Building(self.n, base_supply)
            b.solar_capacity = solar_capacity
            b.is_prosumer = is_prosumer
            b.power_plant_type = power_plant_type
            actual_name = name if name else f"{building_type}_{self.n}"
        
        # 공통 속성 설정
        b.name = actual_name
        b.x, b.y = x, y
        
        # 건물 목록에 추가
        self.buildings.append(b)
        self.n += 1
        return b

    def add_line(self,u,v,cap=5.0,cost=1.0):
        # Check if the indices are valid before creating the line
        if u < 0 or u >= self.n or v < 0 or v >= self.n:
            print(f"Warning: Invalid building indices ({u}, {v}) in add_line. Buildings range is 0-{self.n-1}")
            return None
        if self.buildings[u].removed or self.buildings[v].removed:
            print(f"Warning: Cannot add line between removed buildings ({u}, {v})")
            return None
        
        pl=PowerLine(u,v,cap,cost)
        self.lines.append(pl)
        return pl  # 생성된 PowerLine 객체 반환
    
    def add_wind_plant(self, capacity=80.0, x=0, y=0):
        """풍력발전소 추가 - 중용량 간헐적 발전"""
        b = Building(self.n, 0)
        b.x, b.y = x, y
        b.wind_capacity = capacity
        b.base_supply = capacity * 0.3  # 풍력은 간헐적, 30% 기본 발전
        b.power_plant_type = "wind"
        b.building_type = "wind_plant"
        b.name = f"풍력발전소_{self.n}"
        # 풍력 특성 설정
        b.variability = 0.7  # 높은 변동성
        b.capacity_factor = 0.35  # 35% 설비이용율
        self.buildings.append(b)
        self.n += 1
        return b
    
    def add_solar_plant(self, capacity=60.0, x=0, y=0):
        """태양광발전소 추가 - 중용량 일조 의존 발전"""
        b = Building(self.n, 0)
        b.x, b.y = x, y
        b.solar_capacity = capacity
        b.base_supply = capacity * 0.25  # 태양광은 일조 의존, 25% 기본 발전
        b.power_plant_type = "solar"
        b.building_type = "solar_plant"
        b.name = f"태양광발전소_{self.n}"
        # 태양광 특성 설정
        b.panel_tilt = 35  # 최적 경사각
        b.panel_azimuth = 180  # 남향
        b.capacity_factor = 0.2  # 20% 설비이용율
        self.buildings.append(b)
        self.n += 1
        return b
    
    def add_hydro_plant(self, capacity=100.0, x=0, y=0):
        """수력발전소 추가 - 중대용량 안정 발전"""
        b = Building(self.n, capacity)
        b.x, b.y = x, y
        b.hydro_capacity = capacity
        b.base_supply = capacity * 0.9  # 수력은 매우 안정적, 90% 기본 발전
        b.power_plant_type = "hydro"
        b.building_type = "hydro_plant"
        b.name = f"수력발전소_{self.n}"
        # 수력 특성 설정
        b.reservoir_level = 0.8  # 저수지 수위 80%
        b.capacity_factor = 0.5  # 50% 설비이용율
        b.seasonal_variation = 0.3  # 계절별 변동 30%
        self.buildings.append(b)
        self.n += 1
        return b
    
    def add_hydrogen_storage(self, storage_capacity=100.0, x=0, y=0):
        """그린수소 에너지 저장소 추가"""
        b = Building(self.n, 0)
        b.x, b.y = x, y
        b.hydrogen_storage = storage_capacity
        b.hydrogen_level = storage_capacity * 0.3  # 초기 수소 저장량 30%
        b.power_plant_type = "hydrogen"
        b.building_type = "hydrogen_storage"
        b.base_supply = 1  # 최소 발전량 설정
        b.name = f"수소저장소_{self.n}"
        self.buildings.append(b)
        self.n += 1
        return b
    
    def add_nuclear_plant(self, capacity=200.0, x=0, y=0):
        """원자력발전소 추가 - 대용량 안정 발전"""
        b = Building(self.n, capacity)
        b.x, b.y = x, y
        b.base_supply = capacity * 0.95  # 원자력은 매우 안정적, 95% 기본 발전
        b.power_plant_type = "nuclear"
        b.building_type = "nuclear_plant"
        b.name = f"원자력발전소_{self.n}"
        # 원자력 특성 설정
        b.fuel_efficiency = 0.98  # 높은 연료 효율
        b.maintenance_cost = capacity * 0.1  # 높은 유지비용
        b.reliability = 0.99  # 높은 신뢰도
        self.buildings.append(b)
        self.n += 1
        return b
    
    def add_thermal_plant(self, capacity=150.0, x=0, y=0):
        """화력발전소 추가 - 중대용량 조정 가능 발전"""
        b = Building(self.n, capacity)
        b.x, b.y = x, y
        b.base_supply = capacity * 0.85  # 화력은 85% 기본 발전
        b.power_plant_type = "thermal"
        b.building_type = "thermal_plant"
        b.name = f"화력발전소_{self.n}"
        # 화력 특성 설정
        b.fuel_efficiency = 0.75  # 중간 연료 효율
        b.ramp_rate = 0.8  # 높은 출력 조정 속도
        b.emission_factor = 0.5  # 탄소 배출 계수
        b.fuel_cost = capacity * 0.05  # 연료비용
        self.buildings.append(b)
        self.n += 1
        return b

    def total_demand(self):
        return sum(-b.current_supply for b in self.buildings if b.current_supply<0 and not b.removed)



    ###############################################################################
    # (B) Building, PowerLine, CityGraph 내 build_capacity 함수 (수정본)
    ###############################################################################
    def build_capacity(self):
        """
        CityGraph 클래스 내에 삽입되는 메서드. 
        'self'는 CityGraph 인스턴스.
        """

        print("[build_capacity] 호출됨 - 그래프 용량 구성 시작 --------------------------------")
        S_star = self.n        # 슈퍼소스
        T_star = self.n + 1    # 슈퍼싱크
        n_total = self.n + 2   # 전체 노드(빌딩 n개 + S*, T*)

        # 각 노드별로 (연결노드->capacity) 를 저장할 dict
        cap = [dict() for _ in range(n_total)]

        # 먼저, 송전선 용량 설정
        print("  [build_capacity] 송전선(capacity) 설정 중...")
        for pl in self.lines:
            if pl.removed:
                continue
            if self.buildings[pl.u].removed or self.buildings[pl.v].removed:
                continue
            if pl.capacity > 1e-9:
                # u->v 방향 capacity 지정
                cap[pl.u][pl.v] = pl.capacity
                print(f"    선({pl.u}->{pl.v}), capacity={pl.capacity:.2f}")

        # 각 발전소의 실제 공급 가능량 계산 (연결된 송전선 용량의 합으로 제한)
        print("  [build_capacity] 발전소별 실제 공급 가능량 계산 중...")
        building_max_supply = {}
        for b in self.buildings:
            if b.removed:
                continue
            if b.current_supply > 1e-9:  # 발전소인 경우 (current_supply 기준)
                total_line_capacity = 0
                for pl in self.lines:
                    if pl.removed:
                        continue
                    if self.buildings[pl.u].removed or self.buildings[pl.v].removed:
                        continue
                    if pl.u == b.idx:  # 발전소에서 나가는 선
                        total_line_capacity += pl.capacity
                # 실제 공급 가능량은 current_supply와 송전선 총 용량 중 작은 값
                building_max_supply[b.idx] = min(b.current_supply, total_line_capacity)
                print(f"    발전소{b.idx}: current_supply={b.current_supply:.2f}, 송전선총용량={total_line_capacity:.2f}, 실제가능량={building_max_supply[b.idx]:.2f}")

        # 발전소(양수 current_supply)와 슈퍼소스(S_star) 연결
        print("  [build_capacity] 발전소/수요지 연결 설정 중...")
        for b in self.buildings:
            if b.removed:
                continue
            idx = b.idx
            # 공급 건물 (current_supply 기준)
            if b.current_supply > 1e-9:
                # S_star -> b.idx (실제 공급 가능량으로 제한)
                # building_max_supply 딕셔너리에서 값을 가져오고, 없으면 b.current_supply 사용 (이론적으로는 항상 있어야 함)
                max_supply = building_max_supply.get(idx, b.current_supply) 
                cap[S_star][idx] = max_supply
                print(f"    슈퍼소스 -> {idx}, supply={max_supply:.2f} (current_supply 기반)")

            # 수요 건물(음수)
            elif b.current_supply < -1e-9:
                # b.idx -> T_star
                demand_val = -b.current_supply
                cap[idx][T_star] = demand_val
                print(f"    {idx} -> 슈퍼싱크, demand={demand_val:.2f} (current_supply 기반)")

        print("[build_capacity] 그래프 용량 구성 완료 -----------------------------------------\n")
        return cap, S_star, T_star



    def restore_all(self):
        for b in self.buildings:
            b.removed=False
        for pl in self.lines:
            pl.removed=False
