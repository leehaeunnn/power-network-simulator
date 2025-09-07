from datetime import datetime, timedelta
from city import CityGraph, PowerLine
from data import *
from algorithms import *

class Simulator:
    def __init__(self):
        # 시뮬레이터 내부 상태
        self.city = CityGraph()
        
        # 시나리오 패턴 (ex: peak demand timeline 등)
        self.pattern = None
        
        # 예산, 자금, 이벤트 카운트
        self.budget = 30.0
        self.money = 50.0
        self.event_count = 0
        
        # 시뮬레이션 시간
        self.simTime = datetime(2025,1,1,0,0,0)
        self.gameSpeed = 300.0  # 1초당 5시간 진행(기본값)
        
        # 날씨 시스템
        self.current_weather = "맑음"
        self.weather_duration = 0  # 현재 날씨 유지 시간(분)
        self.solar_efficiency = 1.0  # 태양광 효율
        self.current_temperature = 20.0  # 현재 기온 추적
        self.humidity = 50.0  # 습도 속성 초기화 추가
        self.cloud_factor = 0.0  # 구름량 속성 초기화 추가
        
        # 미세먼지 시스템 추가
        self.current_pm_level = "good"  # 현재 미세먼지 수준
        self.pm_duration = 0  # 현재 미세먼지 수준 유지 시간(분)
        
        # 계절별, 시간대별 수요 배율
        self.season_demand_multiplier = {
            "봄": 1.0,
            "여름": 1.3,
            "가을": 1.0,
            "겨울": 1.2
        }
        self.time_demand_multiplier = [
            0.6,  # 0시
            0.5, 0.4, 0.4, 0.5, 0.7,  # 1-5시
            0.9, 1.1, 1.3, 1.2, 1.1,  # 6-10시
            1.0, 1.0, 1.1, 1.2, 1.3,  # 11-15시
            1.4, 1.5, 1.4, 1.3, 1.2,  # 16-20시
            1.0, 0.8, 0.7  # 21-23시
        ]
        
        # 외부에서 불러올 시나리오 목록
        self.scenarios = []
    
    def set_scenarios(self, scenarios):
        """
        외부에서 JSON을 읽은 뒤 시나리오 리스트를 넘겨받아 보관
        """
        self.scenarios = scenarios
    
    def load_scenario(self, scenario):
        """
        주어진 시나리오 dict를 통해 city, 패턴, 예산, 자금 등을 초기화
        scenario 예: { "name","desc","pattern","buildings","lines","budget","money",... }
        """
        from copy import deepcopy
        self.city = CityGraph()  # 새로 초기화
        self.pattern = deepcopy(scenario.get("pattern", None))
        self.budget = scenario.get("budget", 30.0)
        self.money = scenario.get("money", 50.0)
        self.event_count = 0
        
        # 건물 재구성
        for binfo in scenario["buildings"]:
            b = self.city.add_building(binfo["base_supply"], binfo["x"], binfo["y"])
            b.removed = binfo.get("removed", False)
            b.solar_capacity = binfo.get("solar_capacity", 0.0)
            b.is_prosumer = binfo.get("is_prosumer", False)
            b.building_type = binfo.get("building_type", "apartment")
            b.heating_source = binfo.get("heating_source", "electric")
            b.heating_type = binfo.get("heating_type", "electric")
            b.heating_cop = binfo.get("heating_cop", 1.0)
            b.humidity_sensitivity = binfo.get("humidity_sensitivity", 1.0)
            b.panel_tilt = binfo.get("panel_tilt", 30)
            b.panel_azimuth = binfo.get("panel_azimuth", 180)
        
        # 송전선 재구성
        for linfo in scenario["lines"]:
            pl = PowerLine(linfo["u"], linfo["v"], linfo["capacity"], linfo["cost"])
            pl.removed = linfo.get("removed", False)
            self.city.lines.append(pl)
        
        # 날씨 한번 업데이트
        self.update_weather()
        
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
    
    ############################################
    # 기온/태양위치/태양광 관련 함수들
    ############################################
    
    def get_region_info(self, region):
        """
        지역 정보를 딕셔너리로 리턴 (임의 예시용).
        사실상 data.py에 있는 region_data와 유사한 역할.
        """
        # 간단 예시만 유지
        region_coords = {
            "Seoul":    {"lat": 37.5665, "lon": 126.9780},
            "Busan":    {"lat": 35.1796, "lon": 129.0756},
            "Gangwon":  {"lat": 37.8604, "lon": 128.3115},
            "Daejeon":  {"lat": 36.3504, "lon": 127.3845},
            "Gwangju":  {"lat": 35.1595, "lon": 126.8526},
            "Jeju":     {"lat": 33.4996, "lon": 126.5312}
        }
        if region not in region_coords:
            region = "Seoul"
        
        lat = region_coords[region]["lat"]
        lon = region_coords[region]["lon"]
        
        # 월별 최저/최고 기온(간단 예시)
        base_temp_data_Seoul = {
            1:  {"min": -6,  "max":  2},
            2:  {"min": -3,  "max":  5},
            3:  {"min":  2,  "max": 11},
            4:  {"min":  7,  "max": 17},
            5:  {"min": 12, "max": 23},
            6:  {"min": 17, "max": 27},
            7:  {"min": 22, "max": 29},
            8:  {"min": 23, "max": 30},
            9:  {"min": 18, "max": 26},
            10: {"min": 10, "max": 19},
            11: {"min":  3, "max": 11},
            12: {"min": -2, "max":  5}
        }
        # 지역별 온도 오프셋
        region_temp_offset = {
            "Seoul":   (0, 0),
            "Busan":   (+2, +3),
            "Gangwon": (-3, -2),
            "Daejeon": (0, +1),
            "Gwangju": (+1, +2),
            "Jeju":    (+5, +5)
        }
        off_min, off_max = region_temp_offset[region]
        
        # 이 지역의 월별 temp data 생성
        region_temp_data = {}
        for m in range(1,13):
            region_temp_data[m] = {
                "min": base_temp_data_Seoul[m]["min"] + off_min,
                "max": base_temp_data_Seoul[m]["max"] + off_max
            }
        
        # 간단한 날씨 확률 테이블 (예시)
        base_weather_Seoul = {
            1:  [("맑음", 0.3), ("흐림", 0.3), ("비", 0.1), ("눈", 0.3)],
            2:  [("맑음", 0.4), ("흐림", 0.3), ("비", 0.1), ("눈", 0.2)],
            3:  [("맑음", 0.5), ("흐림", 0.3), ("비", 0.2)],
            4:  [("맑음", 0.5), ("흐림", 0.3), ("비", 0.2)],
            5:  [("맑음", 0.5), ("흐림", 0.3), ("비", 0.2)],
            6:  [("맑음", 0.4), ("흐림", 0.3), ("비", 0.3)],
            7:  [("맑음", 0.3), ("흐림", 0.3), ("비", 0.4)],
            8:  [("맑음", 0.3), ("흐림", 0.3), ("비", 0.4)],
            9:  [("맑음", 0.4), ("흐림", 0.3), ("비", 0.3)],
            10: [("맑음", 0.5), ("흐림", 0.4), ("비", 0.1)],
            11: [("맑음", 0.4), ("흐림", 0.4), ("비", 0.2)],
            12: [("맑음", 0.3), ("흐림", 0.3), ("비", 0.1), ("눈", 0.3)],
        }
        region_weather_offset = {
            "Seoul":   {"맑음":0,"흐림":0,"비":0,"눈":0},
            "Busan":   {"맑음":-0.05,"흐림":0,"비":+0.05,"눈":0},
            "Gangwon": {"맑음":-0.1,"흐림":0,"비":-0.05,"눈":+0.15},
            "Daejeon": {"맑음":0,"흐림":0,"비":0,"눈":0},
            "Gwangju": {"맑음":-0.05,"흐림":+0.05,"비":0,"눈":0},
            "Jeju":    {"맑음":-0.1,"흐림":0,"비":+0.1,"눈":0},
        }
        
        woffset = region_weather_offset[region]
        
        region_weather_table = {}
        for m in range(1,13):
            base_list = base_weather_Seoul[m][:]
            new_list = []
            for (weather_name, prob) in base_list:
                delta = woffset.get(weather_name, 0)
                new_prob = prob + delta
                if new_prob < 0:
                    new_prob = 0
                new_list.append((weather_name, new_prob))
            total_p = sum(p for _,p in new_list)
            if total_p < 1e-9:
                new_list = [("맑음",1.0)]
            else:
                new_list = [(w, p/total_p) for (w,p) in new_list]
            region_weather_table[m] = new_list
        
        return {
            "lat": lat,
            "lon": lon,
            "temp_data": region_temp_data,
            "weather_table": region_weather_table,
            "humidity": {
                1: 59.5, 2: 58.3, 3: 58.1, 4: 59.2, 5: 64.4, 6: 71.7,
                7: 80.3, 8: 78.9, 9: 72.1, 10: 66.3, 11: 62.8, 12: 60.1
            }
        }
    
    def get_sun_position(self, current_time, lat, lon):
        """
        태양 고도각(alt_deg), 방위각(azi_deg)을 근사 계산
        """
        import math
        day_of_year = current_time.timetuple().tm_yday
        hour = current_time.hour + current_time.minute/60.0
        
        deg_to_rad = math.pi/180.0
        rad_to_deg = 180.0/math.pi
        
        B = 360.0*(day_of_year-81)/365.0
        EoT = 9.87*math.sin(2*B*deg_to_rad) - 7.53*math.cos(B*deg_to_rad) - 1.5*math.sin(B*deg_to_rad)
        local_solar_time = hour*60 + 4*(lon) + EoT
        local_solar_hour = local_solar_time/60.0
        hour_angle = 15*(local_solar_hour - 12)
        
        decl = 23.44*math.sin(deg_to_rad*360*(284+day_of_year)/365.0)
        
        lat_r = lat*deg_to_rad
        decl_r = decl*deg_to_rad
        ha_r = hour_angle*deg_to_rad
        
        sin_alt = (math.sin(lat_r)*math.sin(decl_r) + 
                   math.cos(lat_r)*math.cos(decl_r)*math.cos(ha_r))
        alt = math.asin(sin_alt)
        
        cos_azi = (math.sin(decl_r) - math.sin(lat_r)*sin_alt) / (math.cos(lat_r)*math.cos(alt))
        sin_azi = -(math.cos(decl_r)*math.sin(ha_r))/math.cos(alt)
        
        alt_deg = alt*rad_to_deg
        azi = math.atan2(sin_azi, cos_azi)
        azi_deg = azi*rad_to_deg
        azi_deg = azi_deg % 360
        
        return (alt_deg, azi_deg)
    
    def compute_solar_radiation(self, alt_deg, cloud_factor, panel_tilt, panel_azimuth):
        """수정된 태양광 발전량 계산"""
        import math
        
        # 고도각이 음수면 야간 처리
        if alt_deg < 0:
            return 0.0
        
        # 대기 감쇠 계수 (AM: Air Mass)
        try:
            am = 1 / (math.sin(math.radians(alt_deg)) + 0.50572*(6.07995 + alt_deg)**-1.6364)
        except ZeroDivisionError:
            am = 0
        am_factor = 0.7**(am**0.678) if am > 0 else 0

        # 패널 각도 보정 (0~90도 범위 제한)
        panel_tilt = max(0, min(90, panel_tilt))
        incidence_angle = math.radians(abs(panel_tilt - alt_deg))
        tilt_factor = max(0, math.cos(incidence_angle)) * 0.95  # 음수 방지

        # 방위각 보정 (0~360도 범위 제한)
        panel_azimuth = panel_azimuth % 360
        azimuth_diff = abs(panel_azimuth - 180)
        azimuth_factor = max(0, math.cos(math.radians(azimuth_diff * 0.5)))  # 음수 방지

        # 구름 영향 (0~1 범위 강제)
        cloud_factor = max(0, min(1, cloud_factor))
        cloud_effect = 1 - (0.75 * (cloud_factor**1.5))

        # 고온 영향 (25°C 이상시 0.5% per °C)
        temp_effect = 1.0
        if self.current_temperature > 25:
            temp_effect = max(0.5, 1 - 0.005*(self.current_temperature - 25))  # 최소 50% 유지

        # 최종 효율 계산
        raw_irradiance = 1000 * am_factor * tilt_factor * azimuth_factor
        effective_irradiance = raw_irradiance * cloud_effect * temp_effect
        panel_efficiency = 0.20
        output_factor = (effective_irradiance * panel_efficiency) / 1000
        
        return max(0.0, min(1.0, output_factor))
    
    def get_korea_temperature(self, current_time, current_weather):
        """
        지역별(Seoul 가정) 월별 최저/최고 기온 + 일중 사인 변동 + 날씨 영향
        """
        region = "Seoul"
        rinfo = self.get_region_info(region)
        temp_data = rinfo["temp_data"]
        
        m = current_time.month
        base_min = temp_data[m]["min"]
        base_max = temp_data[m]["max"]
        
        import math
        hour = current_time.hour + current_time.minute/60.0
        daily_amp = (base_max - base_min)/2.0
        daily_center = (base_max + base_min)/2.0
        
        random_seed = current_time.day
        daily_random_offset = ((random_seed*13) % 5) - 2
        
        phase = (hour - 15)*(math.pi/12.0)
        temp_variation = daily_amp*math.sin(phase)
        base_temp = daily_center + temp_variation + daily_random_offset
        
        weather_temp_delta = 0
        if current_weather == "비":
            weather_temp_delta = -2
        elif current_weather == "눈":
            weather_temp_delta = -5
        elif current_weather == "흐림":
            if base_temp > 5:
                weather_temp_delta = -1
        
        final_temp = base_temp + weather_temp_delta
        return final_temp
    
    def update_weather(self):
        """
        지역별 날씨 테이블에서 현재 날씨 결정,
        태양광 효율 갱신, 기온 갱신 등
        """
        print("\n[update_weather] 날씨 업데이트 시작 -------------------------------------------------")
        print(f"  현재 시각: {self.simTime}")
        
        import random
        region = getattr(self, "region", "Seoul")  # 시나리오에서 설정된 지역 사용
        rinfo = self.get_region_info(region)
        wtable = rinfo["weather_table"]
        
        m = self.simTime.month
        wlist = wtable[m]
        
        # 날씨 전이 확률 조정 강화
        transition_penalty = {
            "맑음": {"맑음": 0.0, "흐림": 0.0, "비": 0.4, "눈": 0.6},
            "흐림": {"맑음": 0.2, "흐림": 0.3, "비": 0.1, "눈": 0.2},  # 흐림 유지 확률 증가
            "비": {"맑음": 0.4, "흐림": 0.2, "비": 0.3, "눈": 0.5},  # 비 유지 확률 증가
            "눈": {"맑음": 0.6, "흐림": 0.4, "비": 0.5, "눈": 0.2}   # 눈 유지 확률 증가
        }
        
        # 확률 조정
        adjusted_wlist = []
        for (wth, prob) in wlist:
            penalty = transition_penalty.get(self.current_weather, {}).get(wth, 0)
            adj_prob = max(0, prob - penalty)
            adjusted_wlist.append((wth, adj_prob))
        
        # 확률 정규화
        total_prob = sum(p for _, p in adjusted_wlist)
        if total_prob > 0:
            adjusted_wlist = [(w, p/total_prob) for w, p in adjusted_wlist]
        else:
            adjusted_wlist = [("흐림", 1.0)]  # 예외 상황
        
        # 날씨 선택
        r = random.random()
        acc = 0
        chosen = "흐림"  # 기본값
        for (wth, prob) in adjusted_wlist:
            acc += prob
            if r <= acc:
                chosen = wth
                break
        
        old_weather = self.current_weather
        self.current_weather = chosen
        print(f"  날씨 변경: {old_weather} -> {chosen}")
        
        # 태양광 효율 맵 (구름량 기본값 포함)
        weather_effects = {
            "맑음": {"효율": 1.0, "구름": (0.0, 0.2), "기온": 0},
            "흐림": {"효율": 0.5, "구름": (0.3, 0.6), "기온": -1},
            "비": {"효율": 0.2, "구름": (0.5, 0.8), "기온": -2},
            "눈": {"효율": 0.1, "구름": (0.7, 1.0), "기온": -5}
        }
        
        effects = weather_effects.get(chosen, weather_effects["흐림"])
        old_eff = self.solar_efficiency
        self.solar_efficiency = effects["효율"]
        
        # 구름량 설정 (날씨별 범위 내에서)
        cloud_range = effects["구름"]
        self.cloud_factor = random.uniform(cloud_range[0], cloud_range[1])
        
        # 태양 위치 계산 추가
        region_info = self.get_region_info(region)
        lat = region_info["lat"]
        lon = region_info["lon"]
        alt_deg, azi_deg = self.get_sun_position(self.simTime, lat, lon)
        
        # 기온 계산 (구름량 영향 포함)
        temp_now = self.get_korea_temperature(self.simTime, self.current_weather)
        cloud_temp_effect = -1.5 * self.cloud_factor  # 기존 -3 -> -1.5로 조정
        temp_now += cloud_temp_effect + effects["기온"]
        
        old_temp = self.current_temperature
        self.current_temperature = temp_now
        
        # 갑작스러운 온도 변화 방지 (최대 ±5°C 변화)
        temp_diff = temp_now - old_temp
        if abs(temp_diff) > 5:
            temp_now = old_temp + 5 * (temp_diff / abs(temp_diff))
        
        print(f"  기온 변화: {old_temp:.1f}°C -> {temp_now:.1f}°C (구름 영향: {cloud_temp_effect:.1f}°C)")
        
        # 고온에 의한 태양광 효율 감소
        if self.current_temperature > 25:
            over = self.current_temperature - 25
            degrade = 0.004*over
            self.solar_efficiency = max(0.0, self.solar_efficiency*(1.0 - degrade))
            print(f"  고온으로 인한 태양광 효율 감소: {old_eff:.2f} -> {self.solar_efficiency:.2f}")
        else:
            print(f"  태양광 효율: {self.solar_efficiency:.2f}")
        
        # 날씨 유지 시간 증가 (3~6시간)
        self.weather_duration = random.randint(180, 360)
        print(f"  날씨 유지 시간: {self.weather_duration}분")
        
        print(f"  구름량: {self.cloud_factor:.2f}")
        
        # 습도 계산 추가
        monthly_avg_humidity = rinfo["humidity"][m]
        # 습도 변화 완화 (최대 ±5% 변화)
        new_humidity = monthly_avg_humidity * (0.85 + 0.3*random.random())
        humidity_diff = new_humidity - self.humidity
        max_change = 5  # 최대 5% 변화
        if abs(humidity_diff) > max_change:
            new_humidity = self.humidity + max_change * (humidity_diff / abs(humidity_diff))
        self.humidity = new_humidity
        
        print(f"  습도: {self.humidity:.1f}%")
        print(f"  태양광 효율: {self.solar_efficiency*100:.2f}% (상세: {self.compute_solar_radiation(alt_deg, self.cloud_factor, 30, 180)*100:.2f}%)")
        
        # 미세먼지 레벨 업데이트 추가
        self.update_pm_levels()
        
        print("[update_weather] 날씨 업데이트 완료 -------------------------------------------------\n")
    
    def update_pm_levels(self):
        """
        미세먼지 수준을 업데이트하는 함수
        지역별 미세먼지 확률에 따라 새로운 미세먼지 수준 결정
        """
        from random import random, choices
        
        # 미세먼지 지속 시간이 남았으면 유지
        if self.pm_duration > 0:
            self.pm_duration -= 1
            return
        
        # 지역 정보 가져오기
        region = "Seoul"  # 기본 지역
        for scenario in self.scenarios:
            if "region" in scenario:
                region = scenario["region"]
                break
        
        from data import region_data
        if region in region_data and "pm_levels" in region_data[region]:
            pm_data = region_data[region]["pm_levels"]
            
            # 계절에 따른 미세먼지 가중치 적용
            season = self.get_current_season()
            season_pm_factor = {
                "봄": 1.3,  # 봄에 미세먼지 증가
                "여름": 0.7, # 여름에 감소
                "가을": 0.9, # 가을에 약간 감소
                "겨울": 1.4  # 겨울에 크게 증가
            }
            
            # 현재 날씨에 따른 가중치
            weather_pm_factor = {
                "맑음": 1.2,    # 맑을 때 미세먼지 증가 가능성
                "흐림": 0.9,    # 흐릴 때 약간 감소
                "비": 0.4,      # 비 올 때 크게 감소
                "눈": 0.7       # 눈 올 때 감소
            }
            
            season_factor = season_pm_factor.get(season, 1.0)
            weather_factor = weather_pm_factor.get(self.current_weather, 1.0)
            
            # 수정된 확률 계산
            adjusted_pm_levels = {}
            for level, prob in pm_data.items():
                adjusted_pm_levels[level] = prob * season_factor * weather_factor
            
            # 총합이 1이 되도록 정규화
            total = sum(adjusted_pm_levels.values())
            if total > 0:
                adjusted_pm_levels = {k: v / total for k, v in adjusted_pm_levels.items()}
            
            # 미세먼지 수준 선택
            levels = list(adjusted_pm_levels.keys())
            weights = list(adjusted_pm_levels.values())
            self.current_pm_level = choices(levels, weights=weights)[0]
            
            # 지속 시간 설정 (1~6시간)
            self.pm_duration = int(60 + random() * 300)
            
            print(f"미세먼지 수준 변경: {self.current_pm_level}, 지속시간: {self.pm_duration}분")
        else:
            # 기본값 설정
            self.current_pm_level = "moderate"
            self.pm_duration = 120
    
    def get_pm_demand_factor(self, building):
        """
        미세먼지 수준에 따른 전력 수요 가중치 계산
        특히 공기청정기, 환기장치 등의 수요 증가 반영
        """
        # 건물 유형 확인 (없으면 기본값 설정)
        building_type = getattr(building, "building_type", "apartment")
        
        # 미세먼지 수준별 가중치
        pm_demand_multiplier = {
            "good": 1.0,
            "moderate": 1.05,
            "unhealthy": 1.15,
            "very_unhealthy": 1.25,
            "hazardous": 1.4
        }
        
        # 건물 유형별 미세먼지 민감도 가져오기
        from data import building_type_factors
        pm_sensitivity = 1.0
        if building_type in building_type_factors:
            pm_sensitivity = building_type_factors[building_type].get("pm_sensitive", 1.0)
        
        # 미세먼지 수준에 따른 수요 계수 계산
        base_factor = pm_demand_multiplier.get(self.current_pm_level, 1.0)
        
        # 민감도를 반영한 최종 계수
        final_factor = 1.0 + (base_factor - 1.0) * pm_sensitivity
        
        return final_factor
    
    ############################################
    # 수요/공급 패턴
    ############################################
    
    def get_humidity_demand_factor(self, building, month, current_weather):
        """개선된 습도 영향 계산"""
        factor = 1.0
        sens = getattr(building, "humidity_sensitivity", 1.0)
        temp = self.current_temperature
        
        # 절대습도 계산 (단순화된 버전)
        sat_vapor_pressure = 610.78 * math.exp(temp / (temp + 238.3) * 17.2694)
        actual_vapor_pressure = sat_vapor_pressure * (self.humidity/100)
        abs_humidity = 0.622 * actual_vapor_pressure / (101325 - actual_vapor_pressure)
        
        # 계절별 기준값
        if month in [6,7,8]:  # 여름
            if abs_humidity > 0.018:  # 18g/kg 이상
                factor += 0.1 * sens * (abs_humidity - 0.018)/0.005
            if current_weather == "비":
                factor += 0.05 * sens
        elif month in [12,1,2]:  # 겨울
            if abs_humidity < 0.005:  # 5g/kg 미만
                factor += 0.08 * sens * (0.005 - abs_humidity)/0.001
            if current_weather == "눈":
                factor += 0.03 * sens
        
        return factor
    
    def get_temperature_demand_factor(self, temperature, building):
        """개선된 온도 영향 계산"""
        heating_type = getattr(building, "heating_type", "electric")
        cooling_cop = 3.0 if getattr(building, "has_inverter_ac", False) else 2.2
        
        # 난방도일/냉방도일 계산
        if temperature < 18:  # 난방 필요
            hdd = 18 - temperature
            if heating_type == "electric":
                factor = 1 + 0.04*hdd
            elif heating_type == "gas":
                factor = 1 + 0.015*hdd
            else:
                factor = 1 + 0.02*hdd
        elif temperature > 24:  # 냉방 필요
            cdd = temperature - 24
            factor = 1 + (0.05 * cdd)/cooling_cop
        else:
            factor = 1.0
        
        # 일교차 계산 (최고기온 - 최저기온)
        temp_data = self.get_region_info(getattr(self, "region", "Seoul"))["temp_data"][self.simTime.month]
        daily_range = temp_data["max"] - temp_data["min"]  # max와 min의 차이로 계산
        
        if daily_range > 5:
            factor *= 1 + 0.02*(daily_range - 5)/5
        
        return factor
    
    def apply_demand_pattern(self, region="Seoul"):
        """
        - 건물별 수요 계산
        - 태양광 발전량 계산
        """
        print("\n[apply_demand_pattern] 수요 패턴 적용 시작 -------------------------------------------------")
        print(f"  현재 시각: {self.simTime}")
        
        season = self.get_current_season()
        hour = self.simTime.hour
        
        season_mult = self.season_demand_multiplier[season]
        time_mult = self.time_demand_multiplier[hour]
        print(f"  계절({season}): x{season_mult:.2f}")
        print(f"  시간대({hour}시): x{time_mult:.2f}")
        
        # 날씨 영향 강화
        weather_demand_effects = {
            "맑음": 1.0,
            "흐림": 1.05,  # 흐린 날은 실내 활동 증가
            "비": 1.15,    # 비 올 때는 더 큰 영향
            "눈": 1.25     # 눈이 올 때는 가장 큰 영향
        }
        weather_mult = weather_demand_effects.get(self.current_weather, 1.0)
        # 구름량에 따른 추가 영향
        weather_mult *= (1.0 + 0.1 * self.cloud_factor)
        print(f"  날씨({self.current_weather}): x{weather_mult:.2f} (구름량 영향 포함)")
        
        # 태양 위치
        rinfo = self.get_region_info(region)
        lat = rinfo["lat"]
        lon = rinfo["lon"]
        alt_deg, azi_deg = self.get_sun_position(self.simTime, lat, lon)
        print(f"  태양 위치: 고도각={alt_deg:.1f}°, 방위각={azi_deg:.1f}°")
        
        for b in self.city.buildings:
            if b.removed:
                continue
            
            if b.base_supply < 0:
                # 수요 건물
                original_demand = abs(b.base_supply)
                
                temp_factor = self.get_temperature_demand_factor(self.current_temperature, b)
                h_factor = self.get_humidity_demand_factor(b, self.simTime.month, self.current_weather)
                
                total_mult = season_mult * time_mult * weather_mult * temp_factor * h_factor
                new_demand = original_demand * total_mult
                b.current_supply = -new_demand
                print(f"  건물{b.idx}: 기본수요={original_demand:.1f}, 온도x{temp_factor:.2f}, 습도x{h_factor:.2f} => 최종수요={new_demand:.1f}")
            else:
                # 발전소나 중립 건물
                b.current_supply = b.base_supply if b.base_supply > 0 else 0
                
                # 풍력발전소
                if hasattr(b, 'wind_capacity') and b.wind_capacity > 0:
                    wind_speed = 7.0  # 기본 풍속 7m/s
                    if wind_speed < 3:
                        wind_output = 0
                    elif wind_speed > 25:
                        wind_output = 0  # 과풍속 정지
                    else:
                        rated_wind = 12  # 정격 풍속 12m/s
                        wind_factor = min((wind_speed / rated_wind) ** 3, 1.0)
                        wind_output = b.wind_capacity * wind_factor
                    b.current_supply = wind_output
                    print(f"  풍력발전소{b.idx}: 용량={b.wind_capacity:.1f}, 풍속={wind_speed:.1f}m/s => 발전량={wind_output:.1f}")
                
                # 수력발전소
                elif hasattr(b, 'hydro_capacity') and b.hydro_capacity > 0:
                    month = self.simTime.month
                    if month in [6, 7, 8]:  # 여름 (장마철)
                        hydro_factor = 1.2
                    elif month in [12, 1, 2]:  # 겨울 (갈수기)
                        hydro_factor = 0.7
                    else:
                        hydro_factor = 1.0
                    hydro_output = b.hydro_capacity * hydro_factor
                    b.current_supply = hydro_output
                    print(f"  수력발전소{b.idx}: 용량={b.hydro_capacity:.1f}, 계절계수={hydro_factor:.1f} => 발전량={hydro_output:.1f}")
                
                # 태양광발전소 (solar_capacity는 아래에서 별도 처리)
                elif hasattr(b, 'power_plant_type') and b.power_plant_type == 'solar' and hasattr(b, 'base_supply'):
                    # 태양광 발전소도 기본 발전량 설정
                    b.current_supply = b.base_supply if b.base_supply > 0 else 0
                    print(f"  태양광발전소{b.idx}: 기본공급량={b.current_supply:.1f}")
                
                elif b.base_supply > 0:
                    print(f"  발전소{b.idx}: 공급량={b.current_supply:.1f}")
            
            # 태양광
            if getattr(b, "solar_capacity", 0) > 0:
                panel_tilt = getattr(b, "panel_tilt", 30)
                panel_azm = getattr(b, "panel_azimuth", 180)
                cf = getattr(self, "cloud_factor", 0.0)
                solar_factor = self.compute_solar_radiation(alt_deg, cf, panel_tilt, panel_azm)
                solar_output = b.solar_capacity * solar_factor * self.solar_efficiency
                b.current_supply += solar_output
                print(f"  건물{b.idx}: 태양광용량={b.solar_capacity:.1f}, 발전효율={solar_factor:.2f}, 날씨효율={self.solar_efficiency:.2f} => 발전량={solar_output:.1f}")
            
            # 미세먼지 영향 추가
            if b.base_supply < 0:  # 수요 건물인 경우
                pm_factor = self.get_pm_demand_factor(b)
                b.current_supply *= pm_factor
        
        # 수소저장소 처리
        for building in self.city.buildings:
            if building.removed:
                continue
            
            # 수소저장소인 경우
            if building.hydrogen_storage > 0 or (hasattr(building, 'power_plant_type') and building.power_plant_type == 'hydrogen'):
                # 수소저장소와 연결된 발전소 찾기
                connected_power_plants = []
                for line in self.city.lines:
                    if line.removed:
                        continue
                    if line.u == building.idx:
                        other_building = self.city.buildings[line.v]
                        if not other_building.removed and other_building.base_supply > 0:
                            connected_power_plants.append(other_building)
                    elif line.v == building.idx:
                        other_building = self.city.buildings[line.u]
                        if not other_building.removed and other_building.base_supply > 0:
                            connected_power_plants.append(other_building)
                
                # 연결된 발전소가 있을 때만 작동
                if connected_power_plants:
                    # 연결된 발전소들의 잉여 전력 계산
                    connected_generation = sum(plant.current_supply for plant in connected_power_plants)
                    
                    # 전체 시스템의 발전량과 수요량 계산
                    total_generation = sum(b.current_supply for b in self.city.buildings 
                                         if b.current_supply > 0 and not b.removed)
                    total_demand = sum(-b.current_supply for b in self.city.buildings 
                                      if b.current_supply < 0 and not b.removed)
                    
                    # 잉여 전력이 있을 때 수소 생산 (충전)
                    if total_generation > total_demand and connected_generation > 0:  # 잉여 전력이 조금이라도 있으면
                        surplus_power = min((total_generation - total_demand), connected_generation * 0.8)
                        # 수소 생산량 = 잉여전력 * 변환효율
                        hydrogen_efficiency = building.hydrogen_efficiency if hasattr(building, 'hydrogen_efficiency') else 0.6
                        hydrogen_produced = surplus_power * hydrogen_efficiency * 0.1  # 시간당 10%만 변환
                        storage_available = building.hydrogen_storage - building.hydrogen_level
                        
                        if storage_available > 0 and hydrogen_produced > 0:
                            actual_production = min(hydrogen_produced, storage_available)
                            building.hydrogen_level += actual_production
                            # 수소 생산에 사용한 전력은 수요로 계산
                            building.current_supply = -(actual_production / hydrogen_efficiency / 0.1)
                            print(f"  수소저장소 {building.idx}: 잉여전력={surplus_power:.2f}, 수소 생산={actual_production:.2f}, 현재 저장량={building.hydrogen_level:.2f}/{building.hydrogen_storage:.2f}")
                    
                    # 전력 부족 시 수소 연료전지로 발전
                    elif total_demand > total_generation and building.hydrogen_level > 0:  # 전력 부족 시
                        power_shortage = total_demand - total_generation
                        # 수소 발전량 = 저장된 수소 * 변환효율
                        fuel_cell_efficiency = 0.55  # 연료전지 효율
                        max_power_from_hydrogen = building.hydrogen_level * fuel_cell_efficiency
                        
                        actual_generation = min(power_shortage * 0.5, max_power_from_hydrogen)  # 부족분의 50%까지만 보충
                        if actual_generation > 0:
                            hydrogen_consumed = actual_generation / fuel_cell_efficiency
                            building.hydrogen_level -= hydrogen_consumed
                            building.current_supply = actual_generation  # 발전량으로 공급
                            print(f"  수소저장소 {building.idx}: 수소 발전 {actual_generation:.2f}, 현재 저장량 {building.hydrogen_level:.2f}/{building.hydrogen_storage:.2f}")
        
        print("[apply_demand_pattern] 수요 패턴 적용 완료 -------------------------------------------------\n")
    
    ############################################
    # 메인 시뮬레이션 로직 (유량 알고리즘 등)
    ############################################
    
    def compute_line_flows(self):
        """
        건물별 current_supply를 초기화 -> 에드몬드카프 -> 각 라인 flow -> 건물별 공급량 조정
        """
        print("[compute_line_flows] 시작 -------------------------------------------------")
        
        # 우선 모든 건물 current_supply 초기화
        print("  [compute_line_flows] 건물별 current_supply 초기화...")
        for b in self.city.buildings:
            if b.removed:
                continue
            if b.base_supply > 0:
                # 발전소인 경우, 송전선 용량을 고려하여 실제 공급 가능량 계산
                total_line_capacity = 0
                for pl in self.city.lines:
                    if pl.removed:
                        continue
                    if self.city.buildings[pl.u].removed or self.city.buildings[pl.v].removed:
                        continue
                    if pl.u == b.idx:  # 발전소에서 나가는 선
                        total_line_capacity += pl.capacity
                # 실제 공급량은 base_supply와 송전선 총 용량 중 작은 값
                b.current_supply = min(b.base_supply, total_line_capacity)
                b.transmitted_power = 0.0  # 송전량 초기화
                print(f"    발전소{b.idx}: current_supply = {b.current_supply:.2f} (base_supply={b.base_supply:.2f}, 송전선총용량={total_line_capacity:.2f})")
            else:
                # 수요 건물
                b.current_supply = b.base_supply
                print(f"    건물{b.idx}: current_supply = {b.current_supply:.2f}")
        
        # 에드몬드카프 알고리즘으로 최대 유량 계산
        cap, S_star, T_star = self.city.build_capacity()
        flow_val, resid = edmonds_karp(cap, S_star, T_star)
        print(f"  [compute_line_flows] 최대 유량 계산 완료: {flow_val:.2f}")
        
        # 송전선 flow 계산 및 용량 제한 체크
        print("  [compute_line_flows] 송전선별 flow 계산...")
        for pl in self.city.lines:
            if pl.removed:
                pl.flow = 0
                continue
            if self.city.buildings[pl.u].removed or self.city.buildings[pl.v].removed:
                pl.flow = 0
                continue
            
            c_uv = cap[pl.u].get(pl.v,0)
            c_vu = cap[pl.v].get(pl.u,0)
            
            if c_uv > 0:
                r_uv = resid[pl.u].get(pl.v,0)
                used = c_uv - r_uv
                if abs(used) < 1e-9:
                    used = 0
                # 용량 제한 체크
                if used > pl.capacity + 1e-9:
                    print(f"    경고: 송전선({pl.u}->{pl.v}) 용량 초과! flow={used:.2f}, capacity={pl.capacity:.2f}")
                    used = pl.capacity
                pl.flow = used
                if abs(used) > 1e-9:
                    # 발전소의 송전량 추적
                    if self.city.buildings[pl.u].base_supply > 0:
                        self.city.buildings[pl.u].transmitted_power += used
                    self.city.buildings[pl.v].current_supply += used
                print(f"    송전선({pl.u}->{pl.v}): flow={used:.2f}/{pl.capacity:.2f}")
            
            elif c_vu > 0:
                r_vu = resid[pl.v].get(pl.u,0)
                used = c_vu - r_vu
                if abs(used) < 1e-9:
                    used = 0
                # 용량 제한 체크
                if used > pl.capacity + 1e-9:
                    print(f"    경고: 송전선({pl.v}->{pl.u}) 용량 초과! flow={used:.2f}, capacity={pl.capacity:.2f}")
                    used = pl.capacity
                pl.flow = -used
                if abs(used) > 1e-9:
                    # 발전소의 송전량 추적
                    if self.city.buildings[pl.v].base_supply > 0:
                        self.city.buildings[pl.v].transmitted_power += used
                    self.city.buildings[pl.u].current_supply += used
                print(f"    송전선({pl.v}->{pl.u}): flow={used:.2f}/{pl.capacity:.2f}")
            
            else:
                pl.flow = 0
                print(f"    송전선({pl.u}<->{pl.v}): flow=0.00/{pl.capacity:.2f}")
        
        print("[compute_line_flows] 완료 -------------------------------------------------\n")
    
    def check_blackouts(self):
        """
        각 건물의 전력 부족 여부를 검사해서 b.blackout = True/False 설정
        """
        for b in self.city.buildings:
            b.blackout = False
        
        for b in self.city.buildings:
            if b.removed:
                continue
            if b.base_supply < 0:  # 수요 건물
                need = abs(b.base_supply)
                supply = b.current_supply + need  # current_supply는 음수라 need 더하면 실제 공급
                if supply < need - 1e-9:
                    b.blackout = True
    
    def calc_total_flow(self):
        """
        도시 전체 최대흐름(=총 공급량)을 구한다.
        """
        cap, S_star, T_star = self.city.build_capacity()
        flow_val,_ = edmonds_karp(cap, S_star, T_star)
        return flow_val
    
    def update_battery(self):
        """
        건물의 배터리 상태를 업데이트합니다.
        발전량이 많을 때는 배터리를 충전하고, 부족할 때는 방전합니다.
        """
        print("[update_battery] 건물별 배터리 상태 업데이트 시작")
        for b in self.city.buildings:
            if b.removed or b.battery_capacity <= 0:
                continue  # 제거된 건물이나 배터리가 없는 건물은 처리 안함
            
            # 현재 배터리 충전 상태 확인
            charge_percent = (b.battery_charge / b.battery_capacity) * 100
            print(f"  건물{b.idx}: 배터리 {charge_percent:.1f}% 충전 상태 ({b.battery_charge:.1f}/{b.battery_capacity:.1f})")
            
            if b.base_supply > 0:  # 발전소인 경우
                # 배터리 충전 계산
                # 발전량이 송전량보다 많으면 배터리에 충전
                if b.current_supply > b.transmitted_power:
                    excess_power = b.current_supply - b.transmitted_power
                    # 배터리 용량에 따른 최대 충전량 제한
                    max_charge = b.battery_capacity - b.battery_charge
                    charge_amount = min(excess_power, max_charge)
                    
                    if charge_amount > 0:
                        b.battery_charge += charge_amount
                        print(f"    충전: +{charge_amount:.1f} (여유 발전량: {excess_power:.1f})")
                # 배터리 방전 (백업용으로 사용)
                elif b.transmitted_power > b.current_supply and b.battery_charge > 0:
                    shortage = b.transmitted_power - b.current_supply
                    discharge_amount = min(shortage, b.battery_charge)
                    b.battery_charge -= discharge_amount
                    b.current_supply += discharge_amount
                    print(f"    방전: -{discharge_amount:.1f} (부족량: {shortage:.1f})")
                
            else:  # 수요 건물인 경우
                # 피크 시간 여부 확인 (배터리 방전 여부 결정)
                is_peak_time = False
                hour = self.simTime.hour
                if 17 <= hour <= 20:  # 저녁 피크시간
                    is_peak_time = True
                
                # 정전 상태거나 피크 시간이면 배터리 방전
                if b.blackout or is_peak_time:
                    if b.blackout:
                        print(f"    정전 상태: 배터리 긴급 방전")
                    elif is_peak_time:
                        print(f"    피크 시간대: 배터리 사용")
                    
                    # 방전량 계산
                    needed_power = abs(b.current_supply) if b.blackout else min(abs(b.current_supply) * 0.3, b.battery_charge)
                    discharge_amount = min(needed_power, b.battery_charge)
                    
                    if discharge_amount > 0:
                        b.battery_charge -= discharge_amount
                        b.current_supply += discharge_amount  # 음수 수요가 줄어듦
                        print(f"    방전: -{discharge_amount:.1f} (현재 수요: {b.current_supply:.1f})")
                
                # 피크 시간이 아니면서 수요가 적을 때 배터리 충전
                elif not is_peak_time and b.smart_grid_connected:
                    # 기본값 대비 현재 수요 비율 계산
                    demand_ratio = abs(b.current_supply) / abs(b.base_supply) if b.base_supply != 0 else 1.0
                    
                    # 수요가 기본값의 70% 이하일 때 배터리 충전
                    if demand_ratio < 0.7:
                        # 충전량 계산 (최대 기본 수요의 10%)
                        charge_capacity = min(abs(b.base_supply) * 0.1, b.battery_capacity - b.battery_charge)
                        if charge_capacity > 0:
                            # 수요 증가 (음수이므로 더 작아짐)
                            b.current_supply -= charge_capacity
                            b.battery_charge += charge_capacity
                            print(f"    충전: +{charge_capacity:.1f} (수요 증가: {b.current_supply:.1f})")
        
        print("[update_battery] 건물별 배터리 상태 업데이트 완료\n")
    
    def update_flow(self, instant=False):
        """
        송전선 흐름 및 부하 업데이트
        """
        print("[update_flow] 시작")
        # 배터리 시스템 업데이트 (전력 흐름 계산 전에 배터리 방전을 고려)
        self.update_battery()
        
        # 송전선 흐름 계산 실행
        self.compute_line_flows()
        
        # 정전 확인
        self.check_blackouts()
        
        print("[update_flow] 완료\n")
    
    def update_sim_time(self, dt_ms):
        """
        dt_ms: 시뮬레이터 외부(예: Drawer)에서 전달해주는 delta time(ms)
        이 값을 바탕으로 시뮬레이션 시간을 진행.
        """
        dsec = dt_ms / 1000.0
        adv_minutes = dsec * self.gameSpeed
        # 10분 단위로 반올림
        adv_minutes = round(adv_minutes/10.0) * 10
        delta = timedelta(minutes=adv_minutes)
        self.simTime += delta
        
        # 날씨 유지 시간 체크
        self.weather_duration -= adv_minutes
        while self.weather_duration <= 0:
            self.update_weather()
    
    ###################################################
    # 이벤트(랜덤) 관련 함수들 -> 일단 비활성화
    ###################################################
    
    def update_events(self):
        pass
    
    def random_event(self):
        pass
    
    def random_line_trip(self):
        pass
    
    def random_line_half(self):
        pass
    
    def random_bldg_remove(self):
        pass
    
    def random_gen_off(self):
        pass
