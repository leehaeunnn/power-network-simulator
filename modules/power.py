import random
from collections import deque
import math

class PowerSystem:
    def __init__(self, simulator):
        self.simulator = simulator
        self.total_supplied = 0
        self.total_demanded = 0
        self.total_flow = 0
        self.blackout_count = 0
        self.blackout_buildings = []
        self.battery_charge_buildings = []
        self.battery_discharge_buildings = []
        
        # 배터리 저장/방출량
        self.total_battery_storage = 0
        self.total_battery_discharge = 0
        
        # 초기화 시 0으로 설정
        self.update_building_power_stats()
    
    def apply_demand_pattern(self, region="Seoul"):
        """수요 패턴 적용 - 건물별 전력 수요 계산"""
        # 패턴에서 기본 수요 인자 계산
        hour = self.simulator.simTime.hour
        wday = self.simulator.simTime.weekday()
        month = self.simulator.simTime.month
        mday = self.simulator.simTime.day
        
        pattern = self.simulator.pattern
        
        # 패턴이 없으면 기본값 설정
        if not pattern:
            return
            
        # 시간대, 요일, 계절별 인자
        hour_factor = pattern["daily_pattern"][hour]
        weekday_factor = pattern["weekly_pattern"][wday]
        seasonal_factor = pattern["seasonal_pattern"][month-1]
        
        # 휴일 인자 확인
        holiday_factor = 1.0
        for holiday in pattern.get("holiday_list", []):
            if holiday["month"] == month and holiday["day"] == mday:
                holiday_factor = pattern.get("holiday_factor", 1.3)
                break
        
        # 기본 수요 인자
        base_factor = hour_factor * weekday_factor * seasonal_factor * holiday_factor
        
        # 날씨 시스템에서 환경 정보 가져오기
        weather = self.simulator.weather_system
        
        for building in self.simulator.city.buildings:
            if building.removed:
                continue
                
            # 1. 기본 발전/수요 계산
            if building.base_supply <= 0:  # 수요 건물 (상가 포함)
                # 기본 수요
                base_demand = abs(building.base_supply)
                
                # 환경 인자 적용 (온도, 습도, 미세먼지)
                temp_factor = weather.get_temperature_demand_factor(building)
                humidity_factor = weather.get_humidity_demand_factor(building, month)
                pm_factor = weather.get_pm_demand_factor(building)
                
                # 패턴 및 환경 요인 통합 인자
                total_factor = base_factor * temp_factor * humidity_factor * pm_factor
                
                # 건물 유형별 시간대 별도 처리
                if hasattr(building, "building_type"):
                    hour = self.simulator.simTime.hour
                    is_weekend = wday >= 5  # 5(토), 6(일)
                    
                    # 데이터에서 유형별 패턴 가져오기
                    from data import building_type_factors
                    if building.building_type in building_type_factors:
                        type_data = building_type_factors[building.building_type]
                        
                        # 주중/주말, 주간/야간 구분
                        is_night = hour < 6 or hour >= 20
                        
                        if is_weekend and is_night:
                            type_factor = type_data["weekend_night_factor"]
                        elif is_weekend:
                            type_factor = type_data["weekend_day_factor"]
                        elif is_night:
                            type_factor = type_data["weekday_night_factor"]
                        else:
                            type_factor = type_data["weekday_day_factor"]
                        
                        # 건물 유형별 인자 적용
                        total_factor *= type_factor
                
                # 최종 수요 계산
                new_demand = -base_demand * total_factor
                
                # 스마트 그리드 연결된 건물은 피크 시간에 수요 감소
                if hasattr(building, "smart_grid_connected") and building.smart_grid_connected:
                    peak_hours = [9, 10, 11, 17, 18, 19, 20]
                    if hour in peak_hours:
                        new_demand *= 0.85  # 피크 시간 15% 감소
                
                building.current_supply = new_demand
            
            # 2. 발전소인 경우 처리
            elif building.base_supply > 0:
                # 기본 발전량 설정
                building.current_supply = building.base_supply
            
            # 2-1. 풍력발전소 처리
            if building.wind_capacity > 0 or (hasattr(building, 'power_plant_type') and building.power_plant_type == 'wind'):
                # WindPowerPlant 클래스의 메서드 사용 가능 여부 확인
                if hasattr(building, 'calculate_output'):
                    wind_speed = weather.wind_speed if hasattr(weather, 'wind_speed') else 7.0  # 기본 풍속 7m/s
                    wind_output = building.calculate_output(wind_speed)
                else:
                    # 기존 로직 유지
                    wind_speed = weather.wind_speed if hasattr(weather, 'wind_speed') else 5.0  # m/s
                    if wind_speed < 3:
                        wind_output = 0
                    elif wind_speed > 25:
                        wind_output = 0  # 과풍속 정지
                    else:
                        rated_wind = 12  # 정격 풍속 12m/s
                        wind_factor = min((wind_speed / rated_wind) ** 3, 1.0)
                        wind_output = building.wind_capacity * wind_factor
                building.current_supply += wind_output
            
            # 2-2. 수력발전소 처리
            if building.hydro_capacity > 0 or (hasattr(building, 'power_plant_type') and building.power_plant_type == 'hydro'):
                # HydroPowerPlant 클래스의 메서드 사용 가능 여부 확인
                if hasattr(building, 'calculate_output'):
                    # 계절별 수위 변동 계산
                    month = self.simulator.simTime.month
                    if month in [6, 7, 8]:  # 여름 (장마철)
                        water_level_factor = 1.2
                    elif month in [12, 1, 2]:  # 겨울 (갈수기)
                        water_level_factor = 0.7
                    else:
                        water_level_factor = 1.0
                    hydro_output = building.calculate_output(water_level_factor)
                else:
                    # 기존 로직 유지
                    month = self.simulator.simTime.month
                    if month in [6, 7, 8]:  # 여름 (장마철)
                        hydro_factor = 1.2
                    elif month in [12, 1, 2]:  # 겨울 (갈수기)
                        hydro_factor = 0.7
                    else:
                        hydro_factor = 1.0
                    hydro_output = building.hydro_capacity * hydro_factor
                building.current_supply = hydro_output  # 수력은 base_supply를 덮어씀
            
            # 3. 태양광 발전량 추가 계산
            if building.solar_capacity > 0 or (hasattr(building, 'power_plant_type') and building.power_plant_type == 'solar'):
                # SolarPowerPlant 클래스의 메서드 사용 가능 여부 확인
                if hasattr(building, 'calculate_output') and hasattr(building, 'power_plant_type') and building.power_plant_type == 'solar':
                    region_info = weather.get_region_info(region)
                    lat = region_info.get("lat", 37.5665)
                    lon = region_info.get("lon", 126.9780)
                    
                    sun_altitude, sun_azimuth = weather.get_sun_position(self.simulator.simTime, lat, lon)
                    solar_radiation = weather.compute_solar_radiation(
                        sun_altitude, 
                        weather.cloud_factor, 
                        building.panel_tilt, 
                        building.panel_azimuth
                    )
                    
                    temperature = weather.temperature if hasattr(weather, 'temperature') else 25
                    solar_output = building.calculate_output(solar_radiation, temperature)
                else:
                    # 기존 로직 유지
                    region_info = weather.get_region_info(region)
                    lat = region_info.get("lat", 37.5665)  # 서울 기본값
                    lon = region_info.get("lon", 126.9780)
                    
                    # 태양 위치 계산
                    sun_altitude, sun_azimuth = weather.get_sun_position(self.simulator.simTime, lat, lon)
                    
                    # 태양광 발전량 계산
                    solar_radiation = weather.compute_solar_radiation(
                        sun_altitude, 
                        weather.cloud_factor, 
                        building.panel_tilt if hasattr(building, 'panel_tilt') else 35, 
                        building.panel_azimuth if hasattr(building, 'panel_azimuth') else 180
                    )
                    
                    # 날씨 효율 적용
                    solar_output = building.solar_capacity * solar_radiation * weather.solar_efficiency
                
                # 발전량 추가 (수요 건물이면 소비 상쇄, 발전소는 발전량 추가)
                building.current_supply += solar_output
                
                # 프로슈머 건물이 배터리를 가지고 있다면 잉여 전력 저장
                if building.is_prosumer and hasattr(building, 'battery_capacity') and building.battery_capacity > 0 and building.current_supply > 0:
                    surplus = building.current_supply
                    # 배터리 충전 가능 용량 계산
                    charge_capacity = building.battery_capacity - building.battery_charge
                    charge_amount = min(surplus, charge_capacity)
                    
                    if charge_amount > 0:
                        # 충전량은 배터리 용량의 최대 10%로 제한
                        charge_amount = min(charge_capacity, building.battery_capacity * 0.1)
                        
                        # 배터리에는 charge_amount 만큼 저장됨
                        building.battery_charge += charge_amount
                        
                        # 충전에 필요한 전력은 충전 효율을 고려하여 계산 (효율 95% 가정)
                        # 즉, charge_amount를 저장하기 위해 외부에서 charge_amount / 0.95 만큼 전력을 끌어옴
                        required_power_for_charging = charge_amount / 0.95 
                        building.current_supply -= required_power_for_charging # 수요 증가
            
            # 4. 그린수소 에너지 저장소 처리
            if building.hydrogen_storage > 0 or (hasattr(building, 'power_plant_type') and building.power_plant_type == 'hydrogen'):
                hour = self.simulator.simTime.hour
                
                # 수소저장소와 연결된 발전소 찾기
                connected_power_plants = []
                for line in self.simulator.city.lines:
                    if line.removed:
                        continue
                    if line.u == building.idx:
                        other_building = self.simulator.city.buildings[line.v]
                        if not other_building.removed and other_building.base_supply > 0:
                            connected_power_plants.append(other_building)
                    elif line.v == building.idx:
                        other_building = self.simulator.city.buildings[line.u]
                        if not other_building.removed and other_building.base_supply > 0:
                            connected_power_plants.append(other_building)
                
                # HydrogenEnergyStorage 클래스의 메서드 사용 가능 여부 확인
                if hasattr(building, 'charge') and hasattr(building, 'discharge'):
                    # 연결된 발전소가 있을 때만 작동
                    if connected_power_plants:
                        # 연결된 발전소들의 잉여 전력 계산
                        connected_generation = sum(plant.current_supply for plant in connected_power_plants)
                        
                        # 전체 시스템의 발전량과 수요량 계산
                        total_generation = sum(b.current_supply for b in self.simulator.city.buildings 
                                             if b.current_supply > 0 and not b.removed)
                        total_demand = sum(-b.current_supply for b in self.simulator.city.buildings 
                                          if b.current_supply < 0 and not b.removed)
                        
                        print(f"[DEBUG] 수소저장소 {building.idx}: 연결된 발전소 {len(connected_power_plants)}개, 발전량={total_generation:.1f}, 수요량={total_demand:.1f}")
                        
                        # 잉여 전력이 있을 때 수소 생산 (충전)
                        if total_generation > total_demand * 1.1 and connected_generation > 0:  # 10% 이상 잉여
                            surplus_power = min((total_generation - total_demand) * 0.5, connected_generation * 0.8)  # 연결된 발전소 용량의 80%까지만
                            power_consumed = building.charge(surplus_power, duration=1.0)
                            building.current_supply = -power_consumed  # 수소 생산에 사용한 전력 (수요로 계산)
                            print(f"[DEBUG] 수소 생산: 잉여전력={surplus_power:.1f}, 소비전력={power_consumed:.1f}")
                        
                        # 전력 부족 시 수소 연료전지로 발전 (방전)
                        elif total_demand > total_generation * 1.05:  # 5% 이상 부족
                            power_shortage = (total_demand - total_generation) * 0.3  # 부족분의 30%만 보충
                            power_generated = building.discharge(power_shortage, duration=1.0)
                            building.current_supply = power_generated  # 발전량으로 공급
                            print(f"[DEBUG] 수소 발전: 부족전력={power_shortage:.1f}, 발전량={power_generated:.1f}")
                else:
                    # 기존 로직 - 연결된 발전소가 있을 때만 작동
                    if connected_power_plants:
                        # 연결된 발전소들의 잉여 전력 계산
                        connected_generation = sum(plant.current_supply for plant in connected_power_plants)
                        
                        # 전체 시스템의 발전량과 수요량 계산
                        total_generation = sum(b.current_supply for b in self.simulator.city.buildings 
                                             if b.current_supply > 0 and not b.removed)
                        total_demand = sum(-b.current_supply for b in self.simulator.city.buildings 
                                          if b.current_supply < 0 and not b.removed)
                        
                        # 잉여 전력이 있을 때 수소 생산 (전기분해)
                        if total_generation > total_demand * 1.1 and connected_generation > 0:  # 10% 이상 잉여
                            surplus_power = min(total_generation - total_demand, connected_generation * 0.8)  # 연결된 발전소 용량의 80%까지만
                            # 수소 생산량 = 잉여전력 * 변환효율
                            hydrogen_efficiency = building.electrolysis_efficiency if hasattr(building, 'electrolysis_efficiency') else building.hydrogen_efficiency
                            hydrogen_produced = surplus_power * hydrogen_efficiency * 0.1  # 시간당 10%만 변환
                            storage_available = building.hydrogen_storage - building.hydrogen_level
                            
                            if storage_available > 0:
                                actual_production = min(hydrogen_produced, storage_available)
                                building.hydrogen_level += actual_production
                                # 수소 생산에 사용한 전력은 수요로 계산
                                building.current_supply = -(actual_production / hydrogen_efficiency / 0.1)
                        
                        # 전력 부족 시 수소 연료전지로 발전
                        elif total_demand > total_generation * 1.05 and building.hydrogen_level > 0:  # 5% 이상 부족
                            power_shortage = total_demand - total_generation
                            # 수소 발전량 = 저장된 수소 * 변환효율
                            fuel_cell_efficiency = building.fuel_cell_efficiency if hasattr(building, 'fuel_cell_efficiency') else building.hydrogen_efficiency
                            max_power_from_hydrogen = building.hydrogen_level * fuel_cell_efficiency
                            
                            actual_generation = min(power_shortage * 0.5, max_power_from_hydrogen)  # 부족분의 50%까지만 보충
                            if actual_generation > 0:
                                hydrogen_consumed = actual_generation / fuel_cell_efficiency
                                building.hydrogen_level -= hydrogen_consumed
                                building.current_supply = actual_generation  # 발전량으로 공급
    
    def update_battery(self):
        """배터리 충방전 관리"""
        for building in self.simulator.city.buildings:
            if building.removed:
                continue
            # battery_capacity 속성이 없거나 0 이하인 경우 건너뛰기
            if not hasattr(building, 'battery_capacity') or building.battery_capacity <= 0:
                continue
                
            # 프로슈머 건물은 자체 처리 로직이 있으므로 여기서는 스킵
            if building.is_prosumer:
                continue
                
            # 스마트 그리드 연결된 건물의 배터리 관리
            if building.smart_grid_connected:
                hour = self.simulator.simTime.hour
                # 오프피크 시간 (심야, 새벽)에는 충전
                if 1 <= hour <= 5:
                    # 충전 가능량
                    charge_capacity = building.battery_capacity - building.battery_charge
                    if charge_capacity > 0:
                        # 충전량은 배터리 용량의 최대 10%로 제한
                        charge_amount = min(charge_capacity, building.battery_capacity * 0.1)
                        
                        # 배터리에는 charge_amount 만큼 저장됨
                        building.battery_charge += charge_amount
                        
                        # 충전에 필요한 전력은 충전 효율을 고려하여 계산 (효율 95% 가정)
                        # 즉, charge_amount를 저장하기 위해 외부에서 charge_amount / 0.95 만큼 전력을 끌어옴
                        required_power_for_charging = charge_amount / 0.95 
                        building.current_supply -= required_power_for_charging # 수요 증가
                
                # 피크 시간대 방전
                elif hour in [9, 10, 11, 17, 18, 19, 20]:
                    # 현재 수요가 음수인 경우만 (소비 건물)
                    if building.current_supply < 0:
                        discharge_needed = min(-building.current_supply, building.battery_charge)
                        if discharge_needed > 0:
                            building.battery_charge -= discharge_needed
                            # 방전량의 95%만 유효 (5% 손실)
                            building.current_supply += discharge_needed * 0.95
    
    def calc_total_flow(self):
        """총 전력 흐름(실제 공급량) 계산"""
        # 전체 발전량 합계
        total_gen = sum(b.current_supply for b in self.simulator.city.buildings 
                        if b.current_supply > 0 and not b.removed)
        
        # 전체 수요량 합계
        total_dem = sum(-b.current_supply for b in self.simulator.city.buildings 
                        if b.current_supply < 0 and not b.removed)
        
        # 전체 유량 합계
        total_flow = sum(abs(pl.flow) for pl in self.simulator.city.lines if not pl.removed)
        
        # 각 건물의 송전량 기록 (추후 통계용)
        for b in self.simulator.city.buildings:
            b.transmitted_power = 0
        
        # 발전소는 송출량, 소비지는 수신량 합산 (모두 양수로)
        for pl in self.simulator.city.lines:
            if pl.removed:
                continue
            
            u, v = pl.u, pl.v
            flow_value = pl.flow # 부호 있는 값
            abs_flow = abs(flow_value)

            # 건물 객체 가져오기 (인덱스 유효성 점검은 CityGraph.add_line에서 이미 수행됨 가정)
            building_u = self.simulator.city.buildings[u]
            building_v = self.simulator.city.buildings[v]

            if flow_value > 0:  # u -> v 방향 흐름
                if building_u.current_supply > 0: # u가 공급 역할일 때 (발전소 또는 잉여 프로슈머 등)
                    building_u.transmitted_power += abs_flow
                if building_v.current_supply < 0: # v가 수요 역할일 때
                    building_v.transmitted_power += abs_flow 
            elif flow_value < 0:  # v -> u 방향 흐름
                if building_v.current_supply > 0: # v가 공급 역할일 때
                    building_v.transmitted_power += abs_flow
                if building_u.current_supply < 0: # u가 수요 역할일 때
                    building_u.transmitted_power += abs_flow
        
        # === 로그 추가 시작 ===
        # print("  [CalcTotalFlow] 각 건물 transmitted_power 계산 완료:") # 로그 축소
        # for b_log in self.simulator.city.buildings:
        #     if not b_log.removed:
        #         print(f"    - 건물 ID: {b_log.idx}, 이름: {b_log.name}, 타입: {b_log.get_type_str()}, transmitted_power: {b_log.transmitted_power:.2f}") # 로그 축소
        # === 로그 추가 끝 ===

        # 이전 주석: 주의: 이 값은 송전 후 도달한 실제 공급량이 아니라 잠재 흐름 총합임
        
        # simulator.power_system.total_flow는 check_blackouts에서 계산됨
        # 만약 그 값이 아직 없다면 (예: check_blackouts 호출 전) 임시로 계산하거나,
        # 혹은 max_flow (실제 공급된 총량)를 사용하는 것이 더 적절할 수 있음.
        # 여기서는 check_blackouts에서 계산된 total_flow를 신뢰하고 반환.
        # 만약 없다면 0.0 반환 (또는 max_flow 반환 고려)
        
        return_val = 0.0
        source_info = "default 0.0"
        if hasattr(self, 'total_flow') and self.total_flow is not None:
            return_val = self.total_flow
            source_info = "total_flow"
        elif hasattr(self, 'max_flow') and self.max_flow is not None:
            # total_flow가 우선이지만, 없다면 max_flow (실제 시스템에 공급된 총량) 사용
            return_val = self.max_flow
            source_info = "max_flow"
        
        # === 로그 추가 시작 ===
        # total_flow_val_str = f"{self.total_flow:.2f}" if hasattr(self, 'total_flow') and self.total_flow is not None else "N/A"
        # max_flow_val_str = f"{self.max_flow:.2f}" if hasattr(self, 'max_flow') and self.max_flow is not None else "N/A"
        # print(f"  [PowerSystem.calc_total_flow RETURNING] value: {return_val:.2f} (source: {source_info}, current total_flow: {total_flow_val_str}, current max_flow: {max_flow_val_str})") # 로그 축소 (필요시 주석 해제)
        # === 로그 추가 끝 ===
        return return_val
    
    def compute_line_flows(self):
        # print("========== 전력 흐름 계산 시작 ==========")
        # 그래프를 구성하기 위한 노드 추출
        city = self.simulator.city
        buildings = city.buildings
        lines = city.lines
        
        # 발전소 (생산자)와 수요처 (소비자) 찾기
        producers = {}  # 전력을 생산하는 발전소
        consumers = {}  # 전력을 소비하는 건물
        
        for idx, building in enumerate(buildings):
            if not building.removed and building.current_supply > 0:  # 발전소
                producers[idx] = building.current_supply
                # print(f"생산자 {idx}: {building.name}, 발전량: {building.current_supply}") # 로그 축소
            if not building.removed and building.current_supply < 0:  # 수요처
                consumers[idx] = -building.current_supply  # 음수를 양수로 변환
                # print(f"소비자 {idx}: {building.name}, 수요량: {-building.current_supply}") # 로그 축소
        
        # 생산자와 소비자가 있는지 확인
        if not producers:
            # print("경고: 발전소가 없습니다!")
            # 발전소가 없어도 시뮬레이션은 계속 진행
            # 모든 송전선 flow를 0으로 초기화
            for line in lines:
                if not line.removed:
                    line.flow = 0
                    line.usage_rate = 0
            # 블랙아웃 체크는 수행
            self.check_blackouts()
            return
        if not consumers:
            # print("경고: 수요처가 없습니다!")
            # 수요처가 없어도 시뮬레이션은 계속 진행
            for line in lines:
                if not line.removed:
                    line.flow = 0
                    line.usage_rate = 0
            self.check_blackouts()
            return
        
        # 슈퍼소스와 슈퍼싱크 추가
        num_buildings = len(buildings)
        S_star = num_buildings
        T_star = num_buildings + 1
        
        # 그래프 구성: 모든 가능한 엣지를 용량과 함께 저장
        graph = {}
        
        # 모든 노드에 대해 빈 인접 리스트 초기화
        for i in range(num_buildings + 2):  # 건물 + 슈퍼소스 + 슈퍼싱크
            graph[i] = {}
        
        # 슈퍼소스에서 생산자로 연결 (중요: 슈퍼소스 -> 생산자 방향)
        for producer_idx, current_prod_supply in producers.items():
            # 해당 생산자에 연결된 송전선들의 총 용량 합계 계산
            total_line_capacity_for_producer = 0
            # buildings 리스트에서 producer_idx에 해당하는 건물 객체를 직접 사용하기보다는
            # 이미 루프를 돌고 있는 buildings[producer_idx]를 활용하는 것이 안전합니다.
            # (단, producer_idx가 buildings 리스트의 유효한 인덱스임을 보장해야 함 - 현재 producers 딕셔너리 생성 시 idx 사용)
            
            for line_obj in lines: # lines는 city.lines
                if line_obj.removed:
                    continue
                # 연결된 건물이 제거되었는지도 확인
                if buildings[line_obj.u].removed or buildings[line_obj.v].removed:
                    continue
                
                # 양방향 송전선이므로 발전소에 연결된 모든 선의 용량을 고려
                if line_obj.u == producer_idx or line_obj.v == producer_idx:
                    total_line_capacity_for_producer += line_obj.capacity

            # 실제 공급 가능한 최대 용량은 current_supply와 총 회선 용량 중 작은 값
            effective_supply = min(current_prod_supply, total_line_capacity_for_producer)
            
            graph[S_star][producer_idx] = effective_supply
            # print(f"연결: 슈퍼소스 -> 생산자 {producer_idx}, 발전량: {current_prod_supply}, 회선총용량: {total_line_capacity_for_producer}, 실제용량: {effective_supply}") # 로그 축소
        
        # 소비자에서 슈퍼싱크로 연결 (중요: 소비자 -> 슈퍼싱크 방향)
        for consumer_idx, demand in consumers.items():
            graph[consumer_idx][T_star] = demand
            # print(f"연결: 소비자 {consumer_idx} -> 슈퍼싱크, 용량: {demand}") # 로그 축소
        
        # 송전선 연결 추가
        for line in lines:
            if line.removed:
                continue
            if buildings[line.u].removed or buildings[line.v].removed:
                continue
                
            capacity = line.capacity
            u, v = line.u, line.v
            
            # 양방향 송전선으로 설정 - 두 방향 모두 같은 용량 할당
            graph[u][v] = capacity
            if v not in graph: graph[v] = {}
            graph[v][u] = capacity 
            
            # print(f"송전선: {u}({buildings[u].name}) -> {v}({buildings[v].name}), 용량: {capacity}") # 로그 축소
            # print(f"송전선: {v}({buildings[v].name}) -> {u}({buildings[u].name}), 초기용량: 0") # 로그 축소
        
        # Edmonds-Karp 알고리즘으로 최대 유량 계산
        # print("\n최대 유량 계산 시작...") # 로그 축소
        max_flow, flows = self.edmonds_karp(graph, S_star, T_star)
        # print(f"계산된 최대 유량: {max_flow}") # 로그 축소
        
        # 결과를 송전선에 반영
        for line in lines:
            if line.removed:
                continue
            if buildings[line.u].removed or buildings[line.v].removed:
                continue
                
            u, v = line.u, line.v
            
            # flows[(u, v)]는 u에서 v로의 최종 순 흐름(net flow)을 나타냄.
            # (음수일 경우 실제 흐름은 v -> u)
            # 이전 계산 방식: flow_forward = flows.get((u, v), 0); flow_backward = flows.get((v, u), 0); net_flow = flow_forward - flow_backward (오류!)
            actual_net_flow_uv = flows.get((u, v), 0) 

            # line.flow에 이 순 흐름 값을 직접 저장
            line.flow = actual_net_flow_uv
            
            # 사용률 계산
            if line.capacity > 0:
                # 사용률은 흐름의 크기(절대값) 기준
                line.usage_rate = (abs(line.flow) / line.capacity) * 100
            else:
                line.usage_rate = 0
            # 출력문도 명확하게 수정
            # print(f"송전선 {u}({buildings[u].name}) <-> {v}({buildings[v].name}): 최종 흐름(u->v) = {actual_net_flow_uv:.2f}, line.flow = {line.flow:.2f}, 사용률 = {line.usage_rate:.1f}%")
        
        # 총 흐름과 블랙아웃 통계 업데이트
        self.check_blackouts()
        
        # print("========== 전력 흐름 계산 완료 ==========\n")
        
    def edmonds_karp(self, graph, source, sink):
        """Edmonds-Karp 알고리즘으로 최대 유량을 계산합니다."""
        # 흐름을 저장할 딕셔너리 초기화
        flows = {}
        for u in graph:
            for v in graph[u]:
                flows[(u, v)] = 0
        
        # 무한대 값 정의
        INF = float('inf')
        
        # 총 흐름 초기화
        max_flow = 0
        
        while True:
            # BFS로 증가 경로 찾기
            path, path_flow = self.bfs_find_path(graph, flows, source, sink)
            
            # 더 이상 증가 경로가 없으면 종료
            if path_flow == 0:
                break
                
            # 총 흐름 업데이트
            max_flow += path_flow
            
            # 경로를 따라 유량 업데이트
            current = sink
            # print(f"증가 경로 발견: 경로 유량 = {path_flow}") # 로그 축소
            path_str = f"{sink}"
            
            while current != source:
                prev = path[current]
                path_str = f"{prev} -> " + path_str
                
                # 정방향 흐름 증가 또는 역방향 흐름 감소
                flows[(prev, current)] = flows.get((prev, current), 0) + path_flow
                flows[(current, prev)] = flows.get((current, prev), 0) - path_flow
                
                current = prev
            
            # print(f"업데이트된 경로: {path_str}") # 로그 축소
        
        # 흐름과 총 유량 반환
        return max_flow, flows
        
    def bfs_find_path(self, graph, flows, source, sink):
        """BFS로 증가 경로와 그 경로의 최소 용량을 찾습니다."""
        # 경로를 저장할 딕셔너리와 방문 여부 체크
        path = {}
        visited = {source: True}
        
        # BFS 큐 초기화
        queue = deque([source])
        
        # 무한대 값 정의
        INF = float('inf')
        
        while queue and sink not in path:
            u = queue.popleft()
            
            # 현재 노드에서 갈 수 있는 모든 노드 확인
            for v in graph[u]:
                # 잔여 용량 계산
                residual_capacity = graph[u].get(v, 0) - flows.get((u, v), 0)
                
                # 잔여 용량이 있고 아직 방문하지 않은 노드면 경로에 추가
                if residual_capacity > 0 and v not in visited:
                    visited[v] = True
                    path[v] = u
                    queue.append(v)
        
        # 싱크에 도달하지 못했으면 증가 경로 없음
        if sink not in path:
            return {}, 0
        
        # 경로의 최소 용량 찾기
        min_flow = INF
        current = sink
        
        while current != source:
            prev = path[current]
            residual_capacity = graph[prev].get(current, 0) - flows.get((prev, current), 0)
            min_flow = min(min_flow, residual_capacity)
            current = prev
        
        return path, min_flow
    
    def update_building_power_stats(self):
        """각 건물의 전력 공급 상태를 업데이트합니다."""
        # 이 메소드 대신 check_blackouts를 사용
        pass
        
    def check_blackouts(self):
        """각 건물의 정전 상태 확인"""
        city = self.simulator.city
        
        # 모든 건물 정전 상태 및 부족량 초기화
        for b in city.buildings:
            if hasattr(b, 'blackout'):
                b.blackout = False
            if hasattr(b, 'shortage'): # shortage 속성이 Building 클래스에 추가됨
                b.shortage = 0.0
        
        # 수요 건물만 검사
        self.blackout_buildings = []
        
        for b in city.buildings:
            if b.removed or b.current_supply >= 0:
                continue
            
            # 수요량 (양수 값)
            demand = -b.current_supply
            
            # 실제 공급량 (모든 연결된 라인에서 유입되는 전력)
            actual_supply = 0
            # print(f"  [CheckBlackout] 건물 {b.idx}({b.name}) 수요량: {demand:.2f}") # 로그 축소
            for pl in city.lines:
                if pl.removed:
                    continue
                
                # line.flow는 u->v 방향일 때 양수, v->u 방향일 때 음수
                # 건물 b.idx가 pl.v (송전선 끝점)인 경우, pl.u에서 b.idx로 전력이 들어올 수 있음
                if pl.v == b.idx: 
                    if pl.flow > 1e-9: # 실제로 pl.u -> pl.v (b.idx) 흐름이 존재 (양수)
                        actual_supply += pl.flow
                        # print(f"    -> 건물 {b.idx}가 송전선 ({pl.u}->{pl.v}) 끝점(v). flow={pl.flow:.2f}. actual_supply 누적: {actual_supply:.2f}")
                # 건물 b.idx가 pl.u (송전선 시작점)인 경우, pl.v에서 b.idx로 전력이 들어올 수 있음 (역방향 흐름)
                elif pl.u == b.idx: 
                    if pl.flow < -1e-9: # 실제로 pl.v -> pl.u (b.idx) 흐름이 존재 (음수)
                        actual_supply += (-pl.flow) # 음수 값을 양수로 변환하여 더함
                        # print(f"    -> 건물 {b.idx}가 송전선 ({pl.u}-{pl.v}) 시작점(u). flow={pl.flow:.2f} (역방향). actual_supply 누적: {actual_supply:.2f}")
            
            # print(f"  [CheckBlackout] 건물 {b.idx}({b.name}) 최종 actual_supply: {actual_supply:.2f}") # 최종 actual_supply 로그 추가
            # 부족량 계산
            shortage = demand - actual_supply
            if shortage < 1e-9: # 부동소수점 오차 감안하여 0 또는 음수이면 0으로 처리
                shortage = 0.0
            b.shortage = shortage # 계산된 부족량을 건물 객체에 저장
            b.blackout = (actual_supply < demand * 0.8) # 정전 상태 저장

            # === 로그 수정/추가 시작 ===
            # print(f"  [CheckBlackouts] 건물 {b.idx}({b.name}) 최종 actual_supply: {actual_supply:.2f}, 최종 shortage: {b.shortage:.2f}") # 로그 축소
            # === 로그 수정/추가 끝 ===

            # 로그 출력 (디버깅을 위해 블랙아웃 여부와 관계없이 출력)
            shortage_rate = (shortage / demand * 100) if demand > 0 else 0
            if b.blackout:
                self.blackout_buildings.append(b)
                # print(f"[블랙아웃] 건물: {b.name}, 수요={demand:.2f}, 실제공급={actual_supply:.2f}, 부족={shortage:.2f}, 부족률={shortage_rate:.1f}%")
            # else:
                # 블랙아웃 아니어도 정보 출력 (부족량이 0인지 확인용)
                # print(f"[수요정상] 건물: {b.name}, 수요={demand:.2f}, 실제공급={actual_supply:.2f}, 부족={shortage:.2f}, 부족률={shortage_rate:.1f}%")
            
        # 블랙아웃 수 계산
        self.blackout_count = len(self.blackout_buildings)
        
        # 전체 공급량/수요량/흐름량 계산
        self.total_supplied = sum(b.current_supply for b in city.buildings if b.current_supply > 0 and not b.removed)
        self.total_demanded = sum(-b.current_supply for b in city.buildings if b.current_supply < 0 and not b.removed)
        
        # 송전선 흐름의 합 (각 송전선에 흐르는 전력 크기의 합)
        self.total_flow = sum(abs(pl.flow) for pl in city.lines if not pl.removed)
        
        # print(f"전력 통계: 총 공급={self.total_supplied}, 총 수요={self.total_demanded}, 총 흐름={self.total_flow}, 블랙아웃={self.blackout_count}")
    
    def update_flow(self, instant=False):
        """전력 흐름 업데이트"""
        if instant:
            # 즉시 최대 흐름 계산
            self.compute_line_flows()
        else:
            # 일정 확률로 업데이트 (1초에 20% 확률)
            if random.random() < 0.2:
                self.compute_line_flows() 