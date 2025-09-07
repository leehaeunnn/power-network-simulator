import random
import math
from data import region_data

class WeatherSystem:
    def __init__(self, simulator):
        self.simulator = simulator
        
        # 날씨 시스템
        self.current_weather = "맑음"
        self.weather_duration = 0  # 현재 날씨 유지 시간(분)
        self.solar_efficiency = 1.0  # 태양광 효율
        self.current_temperature = 20.0  # 현재 기온 추적
        self.humidity = 50.0  # 습도 속성 초기화 추가
        self.cloud_factor = 0.0  # 구름량 속성 초기화 추가
        self.wind_speed = 5.0  # 풍속 (m/s) 초기화
        
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
    
    def update(self, dt_ms):
        """날씨 시스템 주기적 업데이트"""
        dt_sim_minutes = (dt_ms / 1000.0) * (self.simulator.gameSpeed / 60.0)
        
        # 날씨 지속 시간 감소
        self.weather_duration -= dt_sim_minutes
        if self.weather_duration <= 0:
            self.update_weather()
            
        # 미세먼지 지속 시간 감소
        self.pm_duration -= dt_sim_minutes
        if self.pm_duration <= 0:
            self.update_pm_levels()
            
        # 현재 시간, 날씨에 따른 기온 업데이트
        self.update_temperature()
        
        # 습도 업데이트
        self.update_humidity()
    
    def get_region_info(self, region):
        """지역 정보를 가져옴 (데이터에서)"""
        if region in region_data:
            return region_data[region]
        # 기본값 (서울)
        return region_data["Seoul"]
    
    def get_season(self):
        """현재 계절을 반환"""
        month = self.simulator.simTime.month
        if month in [3, 4, 5]:
            return "봄"
        elif month in [6, 7, 8]:
            return "여름"
        elif month in [9, 10, 11]:
            return "가을"
        else:
            return "겨울"
    
    def get_sun_position(self, current_time, lat, lon):
        """태양 위치 계산 (고도, 방위각)"""
        # 날짜 관련 계산
        day_of_year = current_time.timetuple().tm_yday
        hour = current_time.hour + current_time.minute / 60.0
        
        # 적위 계산 (declination)
        declination = 23.45 * math.sin(math.radians(360.0 * (284 + day_of_year) / 365.0))
        
        # 시간각 계산 (hour angle)
        hour_angle = 15.0 * (hour - 12.0)
        
        # 태양 고도 계산 (altitude)
        sin_alt = (math.sin(math.radians(lat)) * math.sin(math.radians(declination)) + 
                 math.cos(math.radians(lat)) * math.cos(math.radians(declination)) * 
                 math.cos(math.radians(hour_angle)))
        altitude = math.degrees(math.asin(sin_alt))
        
        # 태양 방위각 계산 (azimuth)
        cos_az = ((math.sin(math.radians(declination)) - 
                 math.sin(math.radians(lat)) * math.sin(math.radians(altitude))) / 
                (math.cos(math.radians(lat)) * math.cos(math.radians(altitude))))
        cos_az = max(min(cos_az, 1.0), -1.0)  # 범위 제한 (-1 ~ 1)
        azimuth = math.degrees(math.acos(cos_az))
        
        if hour_angle > 0:
            azimuth = 360 - azimuth
            
        return altitude, azimuth
    
    def compute_solar_radiation(self, alt_deg, cloud_factor, panel_tilt, panel_azimuth):
        """
        태양 고도와 날씨에 따른 태양 복사량 계산
        alt_deg: 태양 고도(도)
        cloud_factor: 구름 정도 (0: 맑음 ~ 1: 완전 흐림)
        panel_tilt: 패널 경사각(도)
        panel_azimuth: 패널 방위각(도)
        """
        if alt_deg <= 0:
            return 0.0  # 밤이면 발전량 없음
        
        # 기본 직달 일사량 (Direct Normal Irradiance, DNI)
        dni = 1000.0 * math.sin(math.radians(alt_deg)) ** 0.7
        
        # 구름에 따른 감쇠
        cloudy_factor = 1.0 - 0.75 * cloud_factor
        dni *= cloudy_factor
        
        # 산란 일사량 (Diffuse Horizontal Irradiance, DHI)
        # 흐린 날은 산란 비율 증가
        dhi_ratio = 0.2 + 0.4 * cloud_factor
        dhi = dni * dhi_ratio
        
        # 패널 방향에 따른 효율 계산
        # 태양 방위각과 패널 방위각의 차이 (남향이 기준, 180도)
        sun_azimuth = 180.0  # 간단화를 위해 항상 남쪽(180도)으로 가정
        azimuth_diff = abs(sun_azimuth - panel_azimuth)
        
        # 방위각 조정 계수
        azimuth_factor = math.cos(math.radians(azimuth_diff))
        azimuth_factor = max(0.5, azimuth_factor)  # 최소 50% 효율 보장
        
        # 패널 경사에 따른 효율
        # 최적 경사각은 위도와 비슷함, 여기서는 30도로 가정
        optimal_tilt = 30.0
        tilt_diff = abs(optimal_tilt - panel_tilt)
        tilt_factor = 1.0 - (tilt_diff / 90.0) * 0.3  # 차이가 커질수록 약간 감소
        
        # 최종 패널에 도달하는 일사량
        panel_irradiance = dni * azimuth_factor * tilt_factor + dhi * 0.5  # DHI는 절반만 적용
        
        # 최종 출력 (W/m²)
        return panel_irradiance / 1000.0  # 정규화된 값 반환 (0~1 범위)
    
    def get_korea_temperature(self, current_time, current_weather):
        """시간, 월, 날씨에 따른 기온 계산"""
        month = current_time.month
        hour = current_time.hour
        
        # 월별 기본 평균 온도 (서울 기준)
        monthly_avg = [
            -2.4, -0.4, 5.7, 12.5, 17.8, 22.2, 24.9, 25.7, 21.2, 14.8, 7.2, -0.4
        ]
        
        # 하루 중 온도 변화 (시간별 편차, 0시 기준)
        hourly_offset = [
            0, -0.5, -1, -1.5, -2, -1.5,  # 0-5시
            -1, 0, 1, 2, 3,               # 6-10시
            3.5, 3.5, 3, 2.5, 2,          # 11-15시
            1, 0.5, 0, -0.5, -1,          # 16-20시
            -1.5, -2, -2.5                # 21-23시
        ]
        
        # 기본 온도 계산
        base_temp = monthly_avg[month - 1] + hourly_offset[hour]
        
        # 날씨에 따른 온도 조정
        weather_offset = {
            "맑음": 2.0,
            "흐림": 0.0,
            "비": -2.0,
            "눈": -4.0
        }
        
        # 최종 온도
        final_temp = base_temp + weather_offset.get(current_weather, 0.0)
        
        # 약간의 무작위성 추가 (±1도)
        final_temp += random.uniform(-1.0, 1.0)
        
        return final_temp
    
    def get_potential_solar_generation_ratio(self):
        """ 현재 시간 및 날씨 조건에서 잠재적인 태양광 발전 비율(0~1)을 반환합니다.
            UI 표시용으로, 이상적인 패널(남향, 최적 경사각)을 가정합니다.
        """
        current_time = self.simulator.simTime
        region_info = self.get_region_info(self.simulator.city.region if hasattr(self.simulator.city, 'region') else "Seoul") # city 객체에 region이 있다면 사용
        lat = region_info.get("lat", 37.5665)
        lon = region_info.get("lon", 126.9780)

        sun_altitude, _ = self.get_sun_position(current_time, lat, lon)

        if sun_altitude <= 0:
            return 0.0 # 밤에는 발전량 0

        # 이상적인 패널 조건 설정 (UI 표시용)
        # 패널 경사각: 해당 지역 위도와 유사하게 (간단히 35도로 가정)
        # 패널 방위각: 남향 (180도)
        ideal_panel_tilt = 35.0 
        ideal_panel_azimuth = 180.0

        # compute_solar_radiation은 이미 0~1 범위의 정규화된 값을 반환함
        # cloud_factor는 현재 날씨에 따라 update_weather에서 설정됨
        potential_radiation = self.compute_solar_radiation(
            sun_altitude,
            self.cloud_factor, 
            ideal_panel_tilt,
            ideal_panel_azimuth
        )
        return potential_radiation
    
    def update_temperature(self):
        """현재 시간과 날씨에 따라 온도 업데이트"""
        target_temp = self.get_korea_temperature(self.simulator.simTime, self.current_weather)
        
        # 현재 온도에서 목표 온도로 서서히 변화
        temp_diff = target_temp - self.current_temperature
        self.current_temperature += temp_diff * 0.1  # 10%씩 타겟에 접근
    
    def update_humidity(self):
        """현재 날씨에 따라 습도 업데이트"""
        # 날씨별 기본 습도
        weather_humidity = {
            "맑음": 40.0 + random.uniform(-5, 5),
            "흐림": 70.0 + random.uniform(-10, 10),
            "비": 85.0 + random.uniform(-5, 10),
            "눈": 75.0 + random.uniform(-10, 5)
        }
        
        # 계절 영향
        season = self.simulator.get_current_season()
        season_humidity_factor = {
            "봄": 1.0,
            "여름": 1.2,  # 여름은 습도 더 높음
            "가을": 0.9,
            "겨울": 0.8   # 겨울은 습도 더 낮음
        }
        
        target_humidity = weather_humidity.get(self.current_weather, 50.0)
        target_humidity *= season_humidity_factor.get(season, 1.0)
        
        # 제한
        target_humidity = max(30.0, min(100.0, target_humidity))
        
        # 현재 습도에서 목표 습도로 서서히 변화
        humidity_diff = target_humidity - self.humidity
        self.humidity += humidity_diff * 0.05  # 5%씩 타겟에 접근
    
    def update_weather(self):
        """날씨 변경 처리 (확률 기반)"""
        current_month = self.simulator.simTime.month
        
        # 날씨 변화 확률 (간단 예시)
        weather_probs = {
            1:  {"맑음": 0.3, "흐림": 0.3, "비": 0.1, "눈": 0.3},  # 1월
            2:  {"맑음": 0.4, "흐림": 0.3, "비": 0.1, "눈": 0.2},
            3:  {"맑음": 0.5, "흐림": 0.3, "비": 0.2, "눈": 0.0},
            4:  {"맑음": 0.5, "흐림": 0.3, "비": 0.2, "눈": 0.0},
            5:  {"맑음": 0.5, "흐림": 0.3, "비": 0.2, "눈": 0.0},
            6:  {"맑음": 0.4, "흐림": 0.3, "비": 0.3, "눈": 0.0},
            7:  {"맑음": 0.3, "흐림": 0.3, "비": 0.4, "눈": 0.0},
            8:  {"맑음": 0.3, "흐림": 0.3, "비": 0.4, "눈": 0.0},
            9:  {"맑음": 0.4, "흐림": 0.3, "비": 0.3, "눈": 0.0},
            10: {"맑음": 0.5, "흐림": 0.4, "비": 0.1, "눈": 0.0},
            11: {"맑음": 0.4, "흐림": 0.4, "비": 0.2, "눈": 0.0},
            12: {"맑음": 0.3, "흐림": 0.3, "비": 0.1, "눈": 0.3}
        }
        
        # 현재 달에 해당하는 확률 가져오기
        month_probs = weather_probs.get(current_month, {"맑음": 0.5, "흐림": 0.3, "비": 0.2, "눈": 0.0})
        
        # 날씨 변화 처리
        weathers = list(month_probs.keys())
        probs = list(month_probs.values())
        self.current_weather = random.choices(weathers, weights=probs, k=1)[0]
        
        # 지속 시간 설정 (30분~4시간)
        self.weather_duration = random.randint(30, 240)
        
        # 구름 계수 업데이트
        if self.current_weather == "맑음":
            self.cloud_factor = random.uniform(0.0, 0.2)
        elif self.current_weather == "흐림":
            self.cloud_factor = random.uniform(0.6, 0.9)
        elif self.current_weather in ["비", "눈"]:
            self.cloud_factor = random.uniform(0.8, 1.0)
            
        # 날씨에 따른 태양광 효율 설정
        weather_efficiency = {
            "맑음": 1.0,
            "흐림": 0.5,
            "비": 0.3,
            "눈": 0.2
        }
        self.solar_efficiency = weather_efficiency.get(self.current_weather, 1.0)
        
        # 날씨에 따른 풍속 업데이트
        if self.current_weather == "맑음":
            self.wind_speed = random.uniform(2.0, 8.0)  # 맑은 날 약한 바람
        elif self.current_weather == "흐림":
            self.wind_speed = random.uniform(5.0, 12.0)  # 흐린 날 중간 바람
        elif self.current_weather == "비":
            self.wind_speed = random.uniform(8.0, 18.0)  # 비오는 날 강한 바람
        elif self.current_weather == "눈":
            self.wind_speed = random.uniform(3.0, 10.0)  # 눈오는 날 중약 바람
        
        # 계절별 풍속 보정
        season_wind_factor = {
            "봄": 1.2,  # 봄철 바람 강함
            "여름": 0.8,  # 여름철 바람 약함
            "가을": 1.1,  # 가을철 바람 중간
            "겨울": 1.3   # 겨울철 바람 강함
        }
        season = self.get_season()
        self.wind_speed *= season_wind_factor.get(season, 1.0)
    
    def update_pm_levels(self):
        """미세먼지 수준 업데이트"""
        # 월별 미세먼지 확률 (간단 예시)
        monthly_pm_prob = {
            1: {"good": 0.2, "moderate": 0.3, "unhealthy": 0.3, "very_unhealthy": 0.15, "hazardous": 0.05},
            2: {"good": 0.15, "moderate": 0.3, "unhealthy": 0.35, "very_unhealthy": 0.15, "hazardous": 0.05},
            3: {"good": 0.1, "moderate": 0.25, "unhealthy": 0.4, "very_unhealthy": 0.2, "hazardous": 0.05},
            4: {"good": 0.2, "moderate": 0.3, "unhealthy": 0.3, "very_unhealthy": 0.15, "hazardous": 0.05},
            5: {"good": 0.3, "moderate": 0.4, "unhealthy": 0.2, "very_unhealthy": 0.05, "hazardous": 0.05},
            6: {"good": 0.4, "moderate": 0.4, "unhealthy": 0.15, "very_unhealthy": 0.03, "hazardous": 0.02},
            7: {"good": 0.5, "moderate": 0.3, "unhealthy": 0.15, "very_unhealthy": 0.03, "hazardous": 0.02},
            8: {"good": 0.5, "moderate": 0.3, "unhealthy": 0.15, "very_unhealthy": 0.03, "hazardous": 0.02},
            9: {"good": 0.4, "moderate": 0.4, "unhealthy": 0.15, "very_unhealthy": 0.03, "hazardous": 0.02},
            10: {"good": 0.35, "moderate": 0.35, "unhealthy": 0.2, "very_unhealthy": 0.07, "hazardous": 0.03},
            11: {"good": 0.25, "moderate": 0.35, "unhealthy": 0.25, "very_unhealthy": 0.1, "hazardous": 0.05},
            12: {"good": 0.2, "moderate": 0.3, "unhealthy": 0.3, "very_unhealthy": 0.15, "hazardous": 0.05}
        }
        
        current_month = self.simulator.simTime.month
        
        # 현재 달에 해당하는 확률 가져오기
        month_probs = monthly_pm_prob.get(current_month, {"good": 0.3, "moderate": 0.3, "unhealthy": 0.3, "very_unhealthy": 0.07, "hazardous": 0.03})
        
        # 날씨에 따른 미세먼지 추가 영향
        weather_pm_modifier = {
            "맑음": {"good": 0.1, "moderate": 0.05, "unhealthy": -0.05, "very_unhealthy": -0.05, "hazardous": -0.05},
            "흐림": {"good": -0.05, "moderate": 0.0, "unhealthy": 0.05, "very_unhealthy": 0.0, "hazardous": 0.0},
            "비": {"good": 0.2, "moderate": 0.1, "unhealthy": -0.1, "very_unhealthy": -0.1, "hazardous": -0.1},
            "눈": {"good": 0.1, "moderate": 0.05, "unhealthy": -0.05, "very_unhealthy": -0.05, "hazardous": -0.05}
        }
        
        weather_mods = weather_pm_modifier.get(self.current_weather, {"good": 0, "moderate": 0, "unhealthy": 0, "very_unhealthy": 0, "hazardous": 0})
        
        # 확률 업데이트
        modified_probs = {}
        for level, prob in month_probs.items():
            modified_probs[level] = max(0.01, min(0.99, prob + weather_mods.get(level, 0)))
            
        # 정규화
        total = sum(modified_probs.values())
        for level in modified_probs:
            modified_probs[level] /= total
        
        # 미세먼지 수준 선택
        levels = list(modified_probs.keys())
        probs = list(modified_probs.values())
        self.current_pm_level = random.choices(levels, weights=probs, k=1)[0]
        
        # 지속 시간 설정 (1시간~12시간)
        self.pm_duration = random.randint(60, 720)
    
    def get_pm_demand_factor(self, building):
        """미세먼지 수준에 따른 전력 수요 인자 계산"""
        pm_factors = {
            "good": 1.0,
            "moderate": 1.05,
            "unhealthy": 1.15,
            "very_unhealthy": 1.25,
            "hazardous": 1.35
        }
        
        # 건물 유형별 민감도
        building_sensitivity = 1.0
        if hasattr(building, "building_type"):
            if building.building_type == "hospital":
                building_sensitivity = 1.5  # 병원은 공기질에 더 민감
            elif building.building_type == "school":
                building_sensitivity = 1.3  # 학교도 민감
                
        base_factor = pm_factors.get(self.current_pm_level, 1.0)
        # 기본값 1.0, 최대 민감도 건물에서 최악의 미세먼지일 때 1.35 * 1.5 = 2.025
        return 1.0 + (base_factor - 1.0) * building_sensitivity
    
    def get_humidity_demand_factor(self, building, month):
        """습도에 따른 전력 수요 인자 계산"""
        # 계절에 따라 적정 습도가 다름
        if 3 <= month <= 5:  # 봄
            optimal_humidity = 50.0
        elif 6 <= month <= 8:  # 여름
            optimal_humidity = 60.0
        elif 9 <= month <= 11:  # 가을
            optimal_humidity = 50.0
        else:  # 겨울
            optimal_humidity = 40.0
            
        # 현재 습도와 적정 습도의 차이
        humidity_diff = abs(self.humidity - optimal_humidity)
        
        # 건물의 습도 민감도
        sensitivity = 1.0
        if hasattr(building, "humidity_sensitivity"):
            sensitivity = building.humidity_sensitivity
            
        # 기본값 1.0, 편차가 크면 전력 소비 증가
        return 1.0 + (humidity_diff / 50.0) * 0.2 * sensitivity
    
    def get_temperature_demand_factor(self, building):
        """온도에 따른 전력 수요 인자 계산"""
        temperature = self.current_temperature
        month = self.simulator.simTime.month
        
        # 계절별 적정 온도
        if 3 <= month <= 5:  # 봄
            optimal_temp = 20.0
        elif 6 <= month <= 8:  # 여름
            optimal_temp = 24.0
        elif 9 <= month <= 11:  # 가을
            optimal_temp = 20.0
        else:  # 겨울
            optimal_temp = 18.0
            
        # 온도 차이에 따른 소비량
        temp_diff = abs(temperature - optimal_temp)
        
        # 냉난방 효율 적용
        efficiency = 1.0
        if hasattr(building, "energy_efficiency"):
            efficiency = building.energy_efficiency
            
        # 히트펌프 효율 적용 (난방시)
        cop = 1.0
        if temperature < optimal_temp and hasattr(building, "heating_type"):
            if building.heating_type == "heat_pump" and hasattr(building, "heating_cop"):
                cop = building.heating_cop
                
        # 수요 계수 계산 (기본 1.0, 온도차가 클수록 증가)
        factor = 1.0 + (temp_diff / 10.0) * 0.3 * efficiency / cop
        
        # 난방이 가스/지역난방인 경우 전기 수요 감소
        if temperature < optimal_temp and hasattr(building, "heating_source"):
            if building.heating_source in ["gas", "district"]:
                factor = 1.0 + (temp_diff / 10.0) * 0.1  # 전기 수요 증가 억제
                
        return factor 