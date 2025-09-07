import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

class SimulationAnalytics:
    def __init__(self, simulator):
        self.simulator = simulator
        self.data_points = []
        self.start_time = simulator.simTime
        self.last_snapshot_time = simulator.simTime
        self.snapshot_interval = timedelta(minutes=30)  # 시뮬레이션 시간 기준 30분마다 데이터 수집
        
        # LLM API 설정 (선택사항)
        self.use_llm_api = False
        self.llm_api_key = os.environ.get("OPENAI_API_KEY", "")
        
        # 초기 데이터 포인트 수집
        self.collect_data_point()
    
    def update(self):
        """주기적으로 시뮬레이션 데이터 수집"""
        current_time = self.simulator.simTime
        
        # 스냅샷 간격 확인
        if current_time - self.last_snapshot_time >= self.snapshot_interval:
            self.collect_data_point()
            self.last_snapshot_time = current_time
    
    def collect_data_point(self):
        """현재 시뮬레이션 상태의 데이터 포인트 수집"""
        sim = self.simulator
        city = sim.city
        
        # 기본 데이터
        data_point = {
            "timestamp": sim.simTime.isoformat(),
            "simulation_minutes": (sim.simTime - self.start_time).total_seconds() / 60,
            "total_demand": abs(city.total_demand()),
            "total_supply": sum(b.current_supply for b in city.buildings if b.current_supply > 0 and not b.removed),
            "total_flow": sim.calc_total_flow(),
            "blackout_count": len([b for b in city.buildings if b.blackout]),
            "weather": sim.weather_system.current_weather,
            "temperature": sim.weather_system.current_temperature,
            "buildings": {
                "total": len(city.buildings),
                "active": len([b for b in city.buildings if not b.removed]),
                "blackout": len([b for b in city.buildings if b.blackout])
            },
            "power_lines": {
                "total": len(city.lines),
                "active": len([pl for pl in city.lines if not pl.removed]),
                "congested": len([pl for pl in city.lines if not pl.removed and abs(pl.flow) / pl.capacity > 0.9])
            },
            "solar_capacity": sum(b.solar_capacity for b in city.buildings if not b.removed),
            "battery_capacity": sum(getattr(b, 'battery_capacity', 0) for b in city.buildings if not b.removed),
            "battery_charge": sum(getattr(b, 'battery_charge', 0) for b in city.buildings if not b.removed)
        }
        
        # 경제 모델 데이터 추가
        if self.simulator.economic_model:
            econ_data = self.simulator.economic_model.get_economic_stats()
            data_point["economics"] = econ_data
        
        # 미세먼지 데이터 추가
        data_point["pm_level"] = sim.weather_system.current_pm_level
        
        # 데이터 포인트 저장
        self.data_points.append(data_point)
    
    def generate_report(self):
        """시뮬레이션 종합 보고서 생성"""
        if not self.data_points:
            return {"error": "데이터 포인트가 없습니다"}
        
        # 마지막 데이터 포인트 가져오기
        last_point = self.data_points[-1]
        
        # 첫 데이터 포인트 가져오기
        first_point = self.data_points[0]
        
        # 평균 계산
        avg_demand = sum(point["total_demand"] for point in self.data_points) / len(self.data_points)
        avg_supply = sum(point["total_supply"] for point in self.data_points) / len(self.data_points)
        avg_blackouts = sum(point["blackout_count"] for point in self.data_points) / len(self.data_points)
        
        # 시뮬레이션 시간 정보
        sim_start = datetime.fromisoformat(first_point["timestamp"])
        sim_end = datetime.fromisoformat(last_point["timestamp"])
        sim_duration = (sim_end - sim_start).total_seconds() / 3600  # 시간 단위
        
        # 주요 지표
        energy_satisfaction = last_point["total_flow"] / max(0.1, last_point["total_demand"]) * 100
        
        # 에너지 믹스
        solar_ratio = last_point["solar_capacity"] / max(0.1, last_point["total_supply"]) * 100
        battery_utilization = last_point["battery_charge"] / max(0.1, last_point["battery_capacity"]) * 100
        
        # 정전 비율
        blackout_ratio = last_point["buildings"]["blackout"] / max(1, last_point["buildings"]["active"]) * 100
        
        # 혼잡 송전선 비율
        congestion_ratio = last_point["power_lines"]["congested"] / max(1, last_point["power_lines"]["active"]) * 100
        
        # 경제 데이터 처리
        if "economics" in last_point:
            econ = last_point["economics"]
            roi = econ.get("roi", 0.0)
            profit = econ.get("profit", 0.0)
            electricity_price = econ.get("electricity_price", 0.0)
        else:
            roi = 0.0
            profit = 0.0
            electricity_price = 0.0
        
        # 보고서 생성
        report = {
            "simulation_period": {
                "start": sim_start.isoformat(),
                "end": sim_end.isoformat(),
                "duration_hours": sim_duration
            },
            "energy_metrics": {
                "current_demand": last_point["total_demand"],
                "current_supply": last_point["total_supply"],
                "current_flow": last_point["total_flow"],
                "avg_demand": avg_demand,
                "avg_supply": avg_supply,
                "energy_satisfaction_percent": energy_satisfaction
            },
            "reliability_metrics": {
                "current_blackouts": last_point["blackout_count"],
                "avg_blackouts": avg_blackouts,
                "blackout_ratio_percent": blackout_ratio,
                "congestion_ratio_percent": congestion_ratio
            },
            "renewable_metrics": {
                "solar_capacity": last_point["solar_capacity"],
                "solar_ratio_percent": solar_ratio,
                "battery_capacity": last_point["battery_capacity"],
                "battery_charge": last_point["battery_charge"],
                "battery_utilization_percent": battery_utilization
            },
            "economic_metrics": {
                "roi_percent": roi,
                "profit": profit,
                "electricity_price": electricity_price
            },
            "environmental_metrics": {
                "current_temperature": last_point["temperature"],
                "current_weather": last_point["weather"],
                "current_pm_level": last_point["pm_level"]
            }
        }
        
        return report
    
    def get_llm_analysis(self):
        """LLM API를 사용하여 시뮬레이션 결과 분석"""
        if not self.use_llm_api or not self.llm_api_key:
            return "LLM API가 설정되지 않았습니다."
            
        try:
            import openai
            
            # API 키 설정
            openai.api_key = self.llm_api_key
            
            # 보고서 생성
            report = self.generate_report()
            
            # API 요청 메시지 구성
            messages = [
                {"role": "system", "content": "전력 네트워크 시뮬레이션 결과를 분석하여 인사이트와 개선점을 제공해주세요."},
                {"role": "user", "content": f"다음은 전력 네트워크 시뮬레이션 결과입니다. 이 결과를 분석하여 주요 인사이트, 문제점, 개선 가능성을 제시해주세요:\n\n{json.dumps(report, indent=2, ensure_ascii=False)}"}
            ]
            
            # API 호출
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"LLM API 호출 중 오류가 발생했습니다: {str(e)}"
    
    def save_data(self, filename):
        """수집된 데이터를 JSON 파일로 저장"""
        data = {
            "simulation_data": self.data_points,
            "report": self.generate_report()
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return f"데이터가 {filename}에 저장되었습니다."
    
    def plot_metrics(self, save_path=None):
        """주요 지표 시각화 및 이미지 저장"""
        if not self.data_points:
            return "데이터 포인트가 없습니다"
            
        # 데이터 추출
        times = [(datetime.fromisoformat(point["timestamp"]) - self.start_time).total_seconds() / 3600 for point in self.data_points]  # 시간 단위
        demands = [point["total_demand"] for point in self.data_points]
        supplies = [point["total_supply"] for point in self.data_points]
        flows = [point["total_flow"] for point in self.data_points]
        blackouts = [point["blackout_count"] for point in self.data_points]
        
        # 온도 데이터
        temperatures = [point["temperature"] for point in self.data_points]
        
        # 경제 데이터가 있으면 추출
        prices = []
        for point in self.data_points:
            if "economics" in point and "electricity_price" in point["economics"]:
                prices.append(point["economics"]["electricity_price"])
            else:
                prices.append(0)
        
        # 그래프 구성
        fig, axs = plt.subplots(3, 1, figsize=(12, 15))
        
        # 1. 전력 수요/공급/흐름
        axs[0].plot(times, demands, label='수요', color='red')
        axs[0].plot(times, supplies, label='공급', color='green')
        axs[0].plot(times, flows, label='흐름', color='blue')
        axs[0].set_xlabel('시뮬레이션 시간 (시간)')
        axs[0].set_ylabel('전력량')
        axs[0].set_title('전력 수요/공급/흐름')
        axs[0].legend()
        axs[0].grid(True)
        
        # 2. 정전 건물 수와 온도
        ax1 = axs[1]
        ax2 = ax1.twinx()
        ax1.plot(times, blackouts, label='정전 건물', color='red')
        ax2.plot(times, temperatures, label='온도', color='orange')
        ax1.set_xlabel('시뮬레이션 시간 (시간)')
        ax1.set_ylabel('정전 건물 수')
        ax2.set_ylabel('온도 (°C)')
        ax1.set_title('정전 건물과 온도')
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        ax1.grid(True)
        
        # 3. 전력 가격
        axs[2].plot(times, prices, label='전력 가격', color='purple')
        axs[2].set_xlabel('시뮬레이션 시간 (시간)')
        axs[2].set_ylabel('전력 가격 (원/kWh)')
        axs[2].set_title('전력 가격 변동')
        axs[2].legend()
        axs[2].grid(True)
        
        plt.tight_layout()
        
        # 이미지 저장 또는 표시
        if save_path:
            plt.savefig(save_path)
            return f"그래프가 {save_path}에 저장되었습니다."
        else:
            plt.show()
            return "그래프가 표시되었습니다." 