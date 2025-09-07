

# -----------------------------------------------------
# 지역별 확장 데이터 테이블 (예: 서울, 인천, 강릉, 춘천)
# 각 지역별: latitude(위도), altitude(해발고도) 추가
# pm_levels: 미세먼지 등급별 확률
# -----------------------------------------------------
region_data = {
    "Seoul": {
        "lat": 37.5665,
        "altitude": 38,  # 해발고도(대략 38m)
        "monthly_avg_temp":  [-2.0, 0.0, 5.0, 12.0, 18.0, 22.0, 26.0, 27.0, 21.0, 14.0, 6.0, 0.0],
        "monthly_daily_range":[ 8.0, 8.0,10.0,10.0, 9.0, 8.0, 6.0, 6.0, 8.0, 9.0,10.0, 8.0],
        "monthly_rain_prob":  [0.15,0.20,0.25,0.30,0.35,0.40,0.55,0.50,0.40,0.30,0.25,0.20],
        # 미세먼지 등급별 확률 예시 (연평균 통계 + 가정)
        "pm_levels": {
            "good": 0.25,
            "moderate": 0.35,
            "unhealthy": 0.20,
            "very_unhealthy": 0.15,
            "hazardous": 0.05
        }
    },
    "Incheon": {
        "lat": 37.4563,
        "altitude": 10,
        "monthly_avg_temp":  [-1.5, 0.5, 5.5, 11.5, 17.5, 21.5, 25.5, 26.5, 20.5, 14.5, 7.0, 1.0],
        "monthly_daily_range":[ 7.0, 7.0, 9.0, 9.0, 8.0, 7.0, 6.0, 6.0, 8.0, 8.0, 9.0, 7.0],
        "monthly_rain_prob":  [0.15,0.18,0.23,0.28,0.33,0.38,0.50,0.45,0.35,0.28,0.23,0.18],
        "pm_levels": {
            "good": 0.20,
            "moderate": 0.40,
            "unhealthy": 0.20,
            "very_unhealthy": 0.15,
            "hazardous": 0.05
        }
    },
    "Gangneung": {
        "lat": 37.7519,
        "altitude": 20,
        "monthly_avg_temp":  [-1.0, 1.0, 6.0, 12.0, 17.5, 21.0, 25.0, 26.0, 20.0, 14.0, 7.0, 2.0],
        "monthly_daily_range":[ 7.0, 7.0, 9.0, 9.0, 8.0, 7.0, 6.0, 6.0, 8.0, 8.0, 9.0, 7.0],
        "monthly_rain_prob":  [0.20,0.25,0.30,0.35,0.38,0.45,0.50,0.50,0.35,0.30,0.25,0.20],
        "pm_levels": {
            "good": 0.30,
            "moderate": 0.40,
            "unhealthy": 0.15,
            "very_unhealthy": 0.10,
            "hazardous": 0.05
        }
    },
    "Chuncheon": {
        "lat": 37.8813,
        "altitude": 75,
        "monthly_avg_temp":  [-3.0, -1.5, 4.0, 11.0, 17.0, 21.0, 25.0, 26.0, 19.5, 13.0, 5.0, -0.5],
        "monthly_daily_range":[10.0,10.0,12.0,12.0,10.0, 9.0, 8.0, 8.0, 9.0,10.0,12.0,10.0],
        "monthly_rain_prob":  [0.16,0.22,0.26,0.30,0.34,0.40,0.50,0.45,0.35,0.28,0.22,0.18],
        "pm_levels": {
            "good": 0.25,
            "moderate": 0.35,
            "unhealthy": 0.20,
            "very_unhealthy": 0.15,
            "hazardous": 0.05
        }
    },
}

# -----------------------------------------------------
# 건물 유형별 파라미터 - 주말/평일, 주간/야간 사용 패턴, 조명 부하 등
#  - weekday_factor: 평일 주간 배율
#  - weekday_night_factor: 평일 야간 배율
#  - weekend_day_factor: 주말 주간 배율
#  - weekend_night_factor: 주말 야간 배율
# -----------------------------------------------------
building_type_factors = {
    "apartment": {
        "heat_factor": 1.0,
        "cool_factor": 1.0,
        "humidity_control_factor": 1.0,
        "pm_sensitive": 0.8,
        "weekday_day_factor": 1.0,
        "weekday_night_factor": 0.9,
        "weekend_day_factor": 1.0,
        "weekend_night_factor": 0.95,
        "lighting_factor": 0.3  # 가정집은 야간 조명 어느정도
    },
    "office": {
        "heat_factor": 1.1,
        "cool_factor": 1.1,
        "humidity_control_factor": 0.8,
        "pm_sensitive": 1.0,
        "weekday_day_factor": 1.0,
        "weekday_night_factor": 0.3,  # 야간에는 거의 사용X
        "weekend_day_factor": 0.2, 
        "weekend_night_factor": 0.1,
        "lighting_factor": 0.5  # 사무실 조명(면적 넓음)
    },
    "school": {
        "heat_factor": 1.2,
        "cool_factor": 1.0,
        "humidity_control_factor": 1.2,
        "pm_sensitive": 1.3,
        "weekday_day_factor": 1.0,
        "weekday_night_factor": 0.1,
        "weekend_day_factor": 0.1,
        "weekend_night_factor": 0.05,
        "lighting_factor": 0.4
    },
    "hospital": {
        "heat_factor": 1.3,
        "cool_factor": 1.2,
        "humidity_control_factor": 1.5,
        "pm_sensitive": 1.5,
        "weekday_day_factor": 1.0,
        "weekday_night_factor": 0.9,
        "weekend_day_factor": 1.0,
        "weekend_night_factor": 0.9,
        "lighting_factor": 0.7  # 병원은 24시간 조명 많음
    },
    "shopping_mall": {
        "heat_factor": 1.1,
        "cool_factor": 1.3,
        "humidity_control_factor": 1.1,
        "pm_sensitive": 1.0,
        "weekday_day_factor": 0.8,
        "weekday_night_factor": 0.4,
        "weekend_day_factor": 1.2,
        "weekend_night_factor": 0.7,
        "lighting_factor": 0.6
    },
}

