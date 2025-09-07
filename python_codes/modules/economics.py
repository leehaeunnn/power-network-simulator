import random
import math
from datetime import datetime, timedelta

class EconomicModel:
    def __init__(self, simulator):
        self.simulator = simulator
        
        # 전력 시장 가격 (원/kWh)
        self.base_electricity_price = 100.0
        self.current_electricity_price = self.base_electricity_price
        self.price_volatility = 0.05  # 가격 변동성
        
        # 수요 응답 가격 체계 (피크 시간 할증)
        self.peak_hours = [9, 10, 11, 12, 17, 18, 19, 20]
        self.peak_price_factor = 1.5
        self.offpeak_hours = [1, 2, 3, 4, 5]
        self.offpeak_price_factor = 0.7
        
        # 탄소 배출권
        self.carbon_price = 30.0  # 원/kg CO2
        self.carbon_emissions = {
            "coal": 0.9,      # kg CO2/kWh
            "gas": 0.4,       # kg CO2/kWh
            "nuclear": 0.0,   # kg CO2/kWh
            "solar": 0.0,     # kg CO2/kWh
            "wind": 0.0       # kg CO2/kWh
        }
        
        # 발전 원가
        self.generation_cost = {
            "coal": 60.0,     # 원/kWh
            "gas": 80.0,      # 원/kWh
            "nuclear": 40.0,  # 원/kWh
            "solar": 5.0,     # 원/kWh (유지보수 비용)
            "wind": 5.0       # 원/kWh (유지보수 비용)
        }
        
        # 설비 투자 비용
        self.infrastructure_cost = {
            "power_line": 100.0,           # 단위 용량당 비용
            "solar_panel": 1000.0,         # kW 당 비용
            "battery": 500.0,              # kWh 당 비용
            "generator": {
                "coal": 2000.0,            # kW 당 비용
                "gas": 1000.0,             # kW 당 비용
                "nuclear": 5000.0,         # kW 당 비용
                "solar_farm": 1500.0,      # kW 당 비용
                "wind_farm": 2000.0        # kW 당 비용
            },
            "smart_grid": 300.0            # 건물당 비용
        }
        
        # 경제 통계
        self.operational_cost = 0.0        # 운영 비용 누적
        self.revenue = 0.0                 # 수익 누적
        self.carbon_tax_paid = 0.0         # 탄소세 누적
        self.investment_cost = 0.0         # 투자 비용 누적
        self.profit = 0.0                  # 순이익
        
        # 발전소 종류 정보 (확장 가능)
        self.generator_types = {}
        
        # 거래 기록
        self.transactions = []
        
        # 가격 변동 추적
        self.price_history = []
        self.last_price_update = simulator.simTime
        
        # 실시간 가격 업데이트 주기 (시뮬레이션 시간 기준, 분)
        self.price_update_interval = 15
    
    def update_energy_prices(self, dt_ms):
        """전력 가격 주기적 업데이트"""
        current_time = self.simulator.simTime
        if (current_time - self.last_price_update).total_seconds() / 60 >= self.price_update_interval:
            self.calculate_electricity_price()
            self.last_price_update = current_time
            
            # 가격 기록 저장
            self.price_history.append({
                "time": current_time.isoformat(),
                "price": self.current_electricity_price
            })
    
    def calculate_electricity_price(self):
        """시간, 수요/공급, 가격 영향 요소 고려하여 전력 가격 계산"""
        hour = self.simulator.simTime.hour
        
        # 기본 가격
        base_price = self.base_electricity_price
        
        # 1. 시간대별 가격 조정
        time_factor = 1.0
        if hour in self.peak_hours:
            time_factor = self.peak_price_factor
        elif hour in self.offpeak_hours:
            time_factor = self.offpeak_price_factor
        
        # 2. 수요/공급 균형에 따른 가격 조정
        supply_demand_factor = self.calculate_supply_demand_factor()
        
        # 3. 날씨 영향
        weather_factor = self.calculate_weather_price_factor()
        
        # 4. 무작위 변동성 추가
        random_factor = random.uniform(1.0 - self.price_volatility, 1.0 + self.price_volatility)
        
        # 최종 가격 계산
        self.current_electricity_price = base_price * time_factor * supply_demand_factor * weather_factor * random_factor
        
        # 가격 범위 제한 (너무 극단적인 값 방지)
        self.current_electricity_price = max(self.base_electricity_price * 0.5, min(self.base_electricity_price * 3.0, self.current_electricity_price))
    
    def calculate_supply_demand_factor(self):
        """수요/공급 비율에 따른 가격 인자 계산"""
        total_demand = abs(self.simulator.city.total_demand())
        
        # 발전 가능량 계산
        total_capacity = sum(b.current_supply for b in self.simulator.city.buildings 
                             if b.current_supply > 0 and not b.removed)
        
        # 송전 제약 고려한 실제 공급량
        total_supply = self.simulator.calc_total_flow()
        
        # 공급 여유율
        if total_demand <= 0:
            reserve_margin = 1.0  # 수요가 없을 경우
        else:
            reserve_margin = total_supply / total_demand
        
        # 여유율에 따른 가격 인자
        if reserve_margin >= 1.3:
            return 0.8  # 충분한 공급, 가격 감소
        elif reserve_margin >= 1.1:
            return 0.9  # 적절한 공급
        elif reserve_margin >= 1.0:
            return 1.1  # 약간 부족
        elif reserve_margin >= 0.9:
            return 1.5  # 상당히 부족
        else:
            return 2.0  # 심각한 부족, 가격 급등
    
    def calculate_weather_price_factor(self):
        """날씨에 따른 가격 영향 계산"""
        weather = self.simulator.weather_system.current_weather
        
        # 날씨별 가격 인자
        weather_factors = {
            "맑음": 0.95,    # 태양광 발전에 유리, 가격 약간 하락
            "흐림": 1.05,    # 태양광 발전 감소, 가격 약간 상승
            "비": 1.1,      # 발전 감소 + 수요 증가 가능성
            "눈": 1.2       # 발전 감소 + 수요 증가 + 송전선 위험 증가
        }
        
        return weather_factors.get(weather, 1.0)
    
    def calculate_carbon_tax(self, energy_type, amount):
        """발전 방식에 따른 탄소세 계산"""
        if energy_type not in self.carbon_emissions:
            return 0.0
            
        emissions = self.carbon_emissions[energy_type] * amount  # kg CO2
        tax = emissions * self.carbon_price  # 원
        
        # 통계 업데이트
        self.carbon_tax_paid += tax
        
        return tax
    
    def calculate_generation_cost(self, energy_type, amount):
        """발전 방식에 따른 발전 비용 계산"""
        if energy_type not in self.generation_cost:
            return 0.0
            
        return self.generation_cost[energy_type] * amount
    
    def calculate_roi(self, investment_type, params):
        """투자 수익률 계산"""
        if investment_type == "power_line":
            capacity = params.get("capacity", 1.0)
            cost = self.infrastructure_cost["power_line"] * capacity
            # 송전선은 직접 수익이 아닌 정전 방지와 흐름 개선을 통한 간접 수익
            estimated_annual_return = capacity * 100  # 단순 추정
            
        elif investment_type == "solar_panel":
            capacity = params.get("capacity", 1.0)
            cost = self.infrastructure_cost["solar_panel"] * capacity
            # 태양광 연간 발전량 추정
            estimated_annual_return = capacity * 1500 * self.base_electricity_price / 1000  # 연 1500시간 가정
            
        elif investment_type == "battery":
            capacity = params.get("capacity", 1.0)
            cost = self.infrastructure_cost["battery"] * capacity
            # 피크/오프피크 차익거래 수익 추정
            price_diff = self.base_electricity_price * (self.peak_price_factor - self.offpeak_price_factor)
            cycles_per_year = 300  # 연간 충방전 사이클
            estimated_annual_return = capacity * price_diff * cycles_per_year
            
        elif investment_type == "smart_grid":
            building_count = params.get("count", 1)
            cost = self.infrastructure_cost["smart_grid"] * building_count
            # 수요 관리를 통한 피크 시간 감소 효과
            estimated_annual_return = building_count * 500  # 단순 추정
            
        else:
            return 0.0, 0.0, 0.0
        
        # ROI 계산
        if cost <= 0:
            return 0.0, 0.0, 0.0
            
        roi = (estimated_annual_return / cost) * 100  # %
        payback_period = cost / estimated_annual_return if estimated_annual_return > 0 else float('inf')  # 년
        
        return roi, payback_period, cost
    
    def make_investment(self, investment_type, params):
        """투자 실행 및 비용 처리"""
        roi, payback, cost = self.calculate_roi(investment_type, params)
        
        # 충분한 예산이 있는지 확인
        if cost > self.simulator.budget:
            return False, "예산 부족"
        
        # 투자 진행
        self.simulator.budget -= cost
        self.investment_cost += cost
        
        # 투자 거래 기록
        self.transactions.append({
            "time": self.simulator.simTime.isoformat(),
            "type": "investment",
            "investment_type": investment_type,
            "amount": cost,
            "params": params
        })
        
        return True, f"투자 완료: {investment_type}, 비용: {cost:.1f}, ROI: {roi:.1f}%, 회수기간: {payback:.1f}년"
    
    def sell_electricity(self, amount, building_type=None):
        """전력 판매 처리 및 수익 계산"""
        if amount <= 0:
            return 0.0
        
        # 건물 유형별 전력 요금 차등
        price_multiplier = 1.0
        if building_type == "hospital":
            price_multiplier = 1.2  # 병원 추가 요금
        elif building_type == "school":
            price_multiplier = 0.9  # 학교 할인
            
        revenue = amount * self.current_electricity_price * price_multiplier / 1000.0  # kWh 단위 변환
        
        # 통계 업데이트
        self.revenue += revenue
        self.profit = self.revenue - self.operational_cost - self.carbon_tax_paid
        
        # 판매 거래 기록
        self.transactions.append({
            "time": self.simulator.simTime.isoformat(),
            "type": "sell",
            "amount": amount,
            "price": self.current_electricity_price,
            "revenue": revenue,
            "building_type": building_type
        })
        
        return revenue
    
    def get_economic_stats(self):
        """경제 통계 데이터 반환"""
        return {
            "electricity_price": self.current_electricity_price,
            "operational_cost": self.operational_cost,
            "revenue": self.revenue,
            "carbon_tax": self.carbon_tax_paid,
            "investment_cost": self.investment_cost,
            "profit": self.profit,
            "roi": (self.profit / max(1.0, self.investment_cost)) * 100 if self.investment_cost > 0 else 0.0
        }
    
    def get_price_history(self):
        """가격 변동 이력 반환"""
        return self.price_history
    
    def get_transactions(self):
        """거래 내역 반환"""
        return self.transactions 