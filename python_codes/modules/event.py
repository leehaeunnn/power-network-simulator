import random

class EventSystem:
    def __init__(self, simulator):
        self.simulator = simulator
        self.event_probability = 0.0001  # 매 업데이트마다 이벤트 발생 확률
        self.event_types = [
            self.random_line_trip,
            self.random_line_half,
            self.random_bldg_remove,
            self.random_gen_off,
            self.random_demand_spike,
            self.random_solar_boost,
            self.random_battery_fault
        ]
        self.last_event_time = None
        self.min_event_interval = 30  # 최소 이벤트 간격(분)
        self.event_history = []
    
    def update_events(self):
        """랜덤 이벤트 발생 확인 및 처리"""
        current_time = self.simulator.simTime
        
        # 마지막 이벤트와의 시간 간격 확인
        if self.last_event_time is not None:
            time_diff = (current_time - self.last_event_time).total_seconds() / 60  # 분 단위
            if time_diff < self.min_event_interval:
                return False  # 최소 간격 미달
        
        # 이벤트 발생 확률 계산 (기본 확률에 시간 흐름 가중치)
        if random.random() < self.event_probability:
            return self.random_event()
            
        return False
    
    def random_event(self):
        """랜덤 이벤트 발생"""
        # 이벤트 타입 랜덤 선택
        event_func = random.choice(self.event_types)
        success = event_func()
        
        if success:
            self.simulator.event_count += 1
            self.last_event_time = self.simulator.simTime
            
            # 이벤트 발생 시 즉시 전력 흐름 업데이트
            self.simulator.update_flow(instant=True)
            
            # 이벤트 기록
            self.event_history.append({
                "time": self.simulator.simTime.isoformat(),
                "type": event_func.__name__,
                "total_count": self.simulator.event_count
            })
            
        return success
    
    def random_line_trip(self):
        """랜덤 송전선 고장 - 일시적 제거"""
        # 활성 상태인 송전선 필터링
        active_lines = [pl for pl in self.simulator.city.lines if not pl.removed]
        
        if not active_lines:
            return False
            
        # 랜덤 선택 후 제거
        target_line = random.choice(active_lines)
        target_line.removed = True
        
        return True
    
    def random_line_half(self):
        """랜덤 송전선 용량 절반으로 감소"""
        active_lines = [pl for pl in self.simulator.city.lines if not pl.removed and pl.capacity > 1.0]
        
        if not active_lines:
            return False
            
        target_line = random.choice(active_lines)
        target_line.capacity /= 2  # 용량 절반으로
        
        return True
    
    def random_bldg_remove(self):
        """랜덤 건물 고장/제거"""
        active_buildings = [b for b in self.simulator.city.buildings if not b.removed]
        
        if not active_buildings:
            return False
            
        target_building = random.choice(active_buildings)
        target_building.removed = True
        
        return True
    
    def random_gen_off(self):
        """랜덤 발전소 용량 감소"""
        generators = [b for b in self.simulator.city.buildings 
                     if not b.removed and b.base_supply > 0]
        
        if not generators:
            return False
            
        target_gen = random.choice(generators)
        # 발전량 20-50% 감소
        reduction = random.uniform(0.2, 0.5)
        target_gen.current_supply *= (1 - reduction)
        
        return True
    
    def random_demand_spike(self):
        """랜덤 소비 건물의 수요 급증"""
        consumers = [b for b in self.simulator.city.buildings 
                    if not b.removed and b.base_supply < 0]
        
        if not consumers:
            return False
            
        target_consumer = random.choice(consumers)
        # 수요 30-80% 증가
        increase = random.uniform(0.3, 0.8)
        target_consumer.current_supply *= (1 + increase)
        
        return True
    
    def random_solar_boost(self):
        """태양광 설비가 있는 건물의 발전량 일시 증가 (맑은 날씨 조건)"""
        if self.simulator.weather_system.current_weather != "맑음":
            return False
            
        solar_buildings = [b for b in self.simulator.city.buildings 
                          if not b.removed and b.solar_capacity > 0]
        
        if not solar_buildings:
            return False
            
        # 모든 태양광 건물에 적용
        for b in solar_buildings:
            if b.current_supply >= 0:  # 발전소나 프로슈머
                b.current_supply += b.solar_capacity * 0.3  # 30% 추가 발전
            else:  # 소비 건물 (태양광 설비가 있는)
                b.current_supply += b.solar_capacity * 0.3  # 수요 상쇄
                
        return True
    
    def random_battery_fault(self):
        """배터리 설비가 있는 건물의 배터리 고장"""
        battery_buildings = [b for b in self.simulator.city.buildings 
                            if not b.removed and hasattr(b, 'battery_capacity') and b.battery_capacity > 0 and hasattr(b, 'battery_charge') and b.battery_charge > 0]
        
        if not battery_buildings:
            return False
            
        target_building = random.choice(battery_buildings)
        # 배터리 충전량 50-100% 손실
        loss_ratio = random.uniform(0.5, 1.0)
        lost_charge = target_building.battery_charge * loss_ratio
        target_building.battery_charge -= lost_charge
        
        return True
    
    def get_event_history(self):
        """이벤트 기록 반환"""
        return self.event_history 