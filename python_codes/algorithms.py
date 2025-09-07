import random
import sys
import pygame
import math
from collections import deque

def edmonds_karp(capacity, source, sink):
    print("[edmonds_karp] 시작 -------------------------------------------------")
    print(f"  source={source}, sink={sink}")
    flow_value = 0
    
    # residual: 각 노드별로 딕셔너리를 만들어 잔여 용량을 저장할 구조
    residual = [dict() for _ in range(len(capacity))]

    # 초기 잔여 용량 설정
    # capacity[u]는 {v: cap_uv, ...} 형태
    print("[edmonds_karp] 초기 residual 그래프 설정")
    for u in range(len(capacity)):
        for v, cap_uv in capacity[u].items():
            # 정방향 잔여 용량
            residual[u][v] = cap_uv
            # 역방향 초기 용량(=0) 설정 (중복 방지 위해 get으로 체크)
            if v not in residual[v] or u not in residual[v]:
                residual[v][u] = 0
    print("[edmonds_karp] 초기 residual 완성")
    
    # 발전소 및 소비자 노드 연결 확인
    print("[edmonds_karp] 발전소 연결 확인:")
    for u, edges in enumerate(capacity):
        if source in edges:
            print(f"  발전소: 노드 {u}, 용량: {capacity[source][u]}")
    
    print("[edmonds_karp] 소비자 연결 확인:")
    for u, edges in enumerate(capacity):
        if sink in edges:
            print(f"  소비자: 노드 {u}, 용량: {capacity[u][sink]}")
    
    # 송전선 연결 확인
    print("[edmonds_karp] 송전선 연결 확인:")
    for u, edges in enumerate(capacity):
        if u != source and u != sink:
            for v, cap in edges.items():
                if v != source and v != sink:
                    print(f"  송전선: {u} -> {v}, 용량: {cap}")
    
    iteration_count = 0
    
    while True:
        iteration_count += 1
        print(f"\n[edmonds_karp] BFS 탐색 시작 (iteration {iteration_count})")
        
        # BFS로 증가 경로 탐색
        parent = [-1] * len(capacity)
        parent[source] = source
        queue = deque([source])
        found_path = False

        while queue and not found_path:
            u = queue.popleft()
            for v in residual[u]:
                # 아직 방문하지 않았고, 잔여 용량이 충분하면 방문
                if residual[u][v] > 1e-9 and parent[v] == -1:
                    parent[v] = u
                    queue.append(v)
                    if v == sink:
                        found_path = True
                        break

        if not found_path:
            print(f"  BFS에서 더 이상 증가 경로를 찾지 못했습니다. 종료.")
            break

        # 증가 경로 재구성 및 bottleneck 계산
        path_nodes = []
        bottleneck = float('inf')
        v = sink
        while v != source:
            path_nodes.append(v)
            u = parent[v]
            bottleneck = min(bottleneck, residual[u][v])
            v = u
        path_nodes.append(source)
        path_nodes.reverse()
        
        print(f"  발견된 증가 경로: {path_nodes}, bottleneck={bottleneck:.4f}")

        # bottleneck만큼 흐름을 흘리고, 역방향 잔여 용량도 갱신
        v = sink
        while v != source:
            u = parent[v]
            residual[u][v] -= bottleneck
            residual[v][u] += bottleneck
            v = u

        flow_value += bottleneck
        print(f"  => flow_value 누적: {flow_value:.4f}")
        # 중간 중간 residual 상태도 간단히 표시(필요시 주석 해제)
        # for i, dic in enumerate(residual):
        #     print(f"   residual[{i}]: {dic}")

    print(f"[edmonds_karp] 최종 최대 유량: {flow_value:.4f}")
    print("[edmonds_karp] 끝 ---------------------------------------------------\n")
    return flow_value, residual

def compute_demand_factor(sim):
    pat=sim.pattern
    hour=sim.simTime.hour
    wday=sim.simTime.weekday()
    month=sim.simTime.month
    mday=sim.simTime.day

    dailyFactor=pat["daily_pattern"][hour]
    weeklyFactor=pat["weekly_pattern"][wday]
    seasonalFactor=pat["seasonal_pattern"][month-1]

    holidayExtra=1.0
    for hd in pat["holiday_list"]:
        if hd["month"]==month and hd["day"]==mday:
            holidayExtra=pat["holiday_factor"]
            break

    totalFactor=dailyFactor*weeklyFactor*seasonalFactor*holidayExtra
    return totalFactor

def compute_solar_factor(sim):
    """태양광 발전량에 영향을 주는 요소들 계산"""
    hour = sim.simTime.hour
    
    # 시간대별 발전 효율 (0시~23시)
    hourly_factor = [
        0.0,  0.0,  0.0,  0.0,  # 0-3시
        0.0,  0.1,  0.3,  0.5,  # 4-7시
        0.7,  0.9,  1.0,  1.0,  # 8-11시
        1.0,  1.0,  0.9,  0.7,  # 12-15시
        0.5,  0.3,  0.1,  0.0,  # 16-19시
        0.0,  0.0,  0.0,  0.0   # 20-23시
    ]
    
    # 계절별 보정
    month = sim.simTime.month
    if 3 <= month <= 5:     # 봄
        season_factor = 1.0
    elif 6 <= month <= 8:   # 여름
        season_factor = 1.2
    elif 9 <= month <= 11:  # 가을
        season_factor = 0.8
    else:                   # 겨울
        season_factor = 0.6
        
    return hourly_factor[hour] * season_factor

def apply_demand_pattern(sim):
    factor=compute_demand_factor(sim)
    for b in sim.city.buildings:
        if b.removed:
            continue
            
        if b.base_supply <= 0:  # 수요 건물 (상가 포함)
            base = abs(b.base_supply)
            newDem = -base * factor
            b.current_supply = newDem
            
            # 태양광이 있다면 발전량 추가 (자체 소비 상쇄)
            if b.solar_capacity > 0:
                solar_factor = compute_solar_factor(sim)
                b.current_supply += b.solar_capacity * solar_factor
                
        else:  # 발전소
            # 기본 발전량 설정
            b.current_supply = b.base_supply
            
            # 태양광이 있다면 발전량 추가
            if b.solar_capacity > 0:
                solar_factor = compute_solar_factor(sim)
                b.current_supply += b.solar_capacity * solar_factor

def simple_upgrade_ai(sim,budget=30.0):
    steps=0
    while steps<100:
        flow_val=sim.calc_total_flow()
        dem=sim.city.total_demand()
        if flow_val>=dem-1e-9:
            break
        if budget<=0:
            break

        best_line=None
        best_usage=0
        for pl in sim.city.lines:
            if pl.removed:
                continue
            if sim.city.buildings[pl.u].removed or sim.city.buildings[pl.v].removed:
                continue
            if pl.capacity<1e-9:
                continue
            usage=abs(pl.flow)/pl.capacity
            if usage>best_usage:
                best_usage=usage
                best_line=pl

        if best_line and best_usage>0.5:
            add_cap=2.0
            cost_need=best_line.cost*add_cap
            if cost_need>budget:
                add_cap=budget/best_line.cost
                cost_need=budget
            best_line.capacity+=add_cap
            budget-=cost_need
            sim.update_flow(instant=True)
            steps+=1
        else:
            gens=[b for b in sim.city.buildings if b.base_supply>0 and not b.removed]
            if gens and budget>=2:
                g=random.choice(gens)
                g.base_supply+=0.5
                g.current_supply=g.base_supply
                budget-=2
                sim.update_flow(instant=True)
                steps+=1
            else:
                break


                import numpy as np

# Constants
alpha_0 = 1e-4   
beta = 5e-5     
R = 0.2          
R_thermal_cold = 0.1  
R_thermal_hot = 0.1   
T_hot = 300      
T_cold = 273     
T_diff = T_hot - T_cold  

#주어진 온도의 제벡계수 계산.
def seebeck_coefficient(T):
    """
    제벡계수를 계산한ㄷr..........
    """
    return alpha_0 * (1 + beta * T)

# COP 계산.
def calculate_peltier_cop(alpha_0, beta, R, R_thermal_cold, R_thermal_hot, T_hot, T_cold):
    """
    아래를 적용한 COP를 계산한ㄷr..구체적 상황 적용..
    - Temperature-dependent Seebeck coefficient
    - Thermal resistances on cold and hot sides
    - Joule heating effect
    """
    I = 1.0  
    
    # 각 구간 온도차에 따른 계수 적용
    alpha_hot = seebeck_coefficient(T_hot)
    alpha_cold = seebeck_coefficient(T_cold)
    # 전달된 열
    Q_cold = alpha_cold * I * T_diff  
    P_joule = I**2 * R 
    # 줄 히팅을 포함한 총 전력량
    P_elec = I**2 * R + P_joule  
    
    # 열적 저항 적용.
    Q_hot = (T_hot - T_cold) / (R_thermal_cold + R_thermal_hot)  
    COP = Q_cold / P_elec
    
    COP_carnot = T_cold / (T_hot - T_cold)

    # Output detailed information
    print(f"Seebeck coefficient at hot side: {alpha_hot:.6f} V/K")
    print(f"Seebeck coefficient at cold side: {alpha_cold:.6f} V/K")
    print(f"Joule heating power (P_joule): {P_joule:.2f} W")
    print(f"Electrical power input (P_elec): {P_elec:.2f} W")
    print(f"Heat removed from the cold side (Q_cold): {Q_cold:.2f} W")
    print(f"Heat dissipated through thermal resistances (Q_hot): {Q_hot:.2f} W")
    print(f"Coefficient of Performance (COP): {COP:.2f}")
    print(f"Carnot efficiency (COP_Carnot): {COP_carnot:.2f}")
    
    return COP, COP_carnot

# Calculate COP
COP, COP_carnot = calculate_peltier_cop(alpha_0, beta, R, R_thermal_cold, R_thermal_hot, T_hot, T_cold)

# Output the result
if COP > COP_carnot:
    print("Warning: COP exceeds the Carnot limit! Check your parameters.")
else:
    print("COP is within the expected range compared to Carnot limit.")

def analyze_current_grid_status(simulator):
    """현재 시뮬레이터의 전력망 상태를 분석하여 구조화된 결과와 요약 메시지를 반환합니다."""
    problems = []
    city = simulator.city
    power_system = simulator.power_system
    overall_severity_score = 0 # 전체 심각도 점수 (0.0 ~ 1.0)

    print("[DEBUG-ANALYSIS] 전력망 상태 분석 시작")
    print(f"[DEBUG-ANALYSIS] 빌딩 수: {len(city.buildings)}, 송전선 수: {len(city.lines) if hasattr(city, 'lines') else '알 수 없음'}")

    # 1. 과부하 송전선 분석
    overloaded_lines_found = False
    if hasattr(city, 'lines'):
        print("[DEBUG-ANALYSIS] 송전선 부하 상태:")
        for line in city.lines:
            if not line.removed and line.capacity > 1e-9:
                usage_rate = (abs(line.flow) / line.capacity)
                usage_pct = usage_rate * 100
                print(f"  - 송전선 {line.u}-{line.v}: 흐름={line.flow:.2f}, 용량={line.capacity:.2f}, 사용률={usage_pct:.1f}%")
                
                if usage_rate > 0.8: # 80% 이상 사용 시
                    overloaded_lines_found = True
                    severity = 0.0
                    if usage_rate > 0.95: # 95% 초과
                        severity = 0.9 + (usage_rate - 0.95) * 2 # 0.9 ~ 1.0
                    elif usage_rate > 0.90: # 90% 초과
                        severity = 0.7 + (usage_rate - 0.90) * 4 # 0.7 ~ 0.9
                    else: # 80% 초과
                        severity = 0.5 + (usage_rate - 0.80) * 2 # 0.5 ~ 0.7
                    
                    problems.append({
                        'type': 'overloaded_line',
                        'description': f"송전선 {line.u}-{line.v}: 사용률 {(usage_rate*100):.1f}% (용량: {line.capacity:.1f}, 현재: {abs(line.flow):.1f})",
                        'severity': round(min(max(severity, 0.0), 1.0), 2),
                        'entities': [f"line_{line.u}_{line.v}"] # u,v 대신 고유 ID가 있다면 그것을 사용
                    })
                    overall_severity_score = max(overall_severity_score, severity)
        
        if not overloaded_lines_found:
            print(f"[DEBUG-ANALYSIS] 과부하 송전선(80% 이상)이 감지되지 않음")
    else:
        print(f"[DEBUG-ANALYSIS] 송전선 정보를 찾을 수 없음")

    # 2. 정전 건물 분석
    blackout_building_details = []
    total_affected_demand_blackout = 0
    blackout_severity_contribution = 0
    if hasattr(power_system, 'blackout_buildings') and power_system.blackout_buildings:
        num_blackout_buildings = len(power_system.blackout_buildings)
        for b in power_system.blackout_buildings:
            if hasattr(b, 'name') and hasattr(b, 'shortage'):
                blackout_building_details.append(f"{b.name}: 부족량 {b.shortage:.1f}")
                total_affected_demand_blackout += b.shortage
        
        if num_blackout_buildings > 0:
            # 심각도: 정전 건물 수와 총 피해 수요량 고려
            # 예를 들어, 전체 수요 대비 피해 수요 비율 등을 사용할 수 있음
            current_total_demand = city.total_demand()
            severity_by_count = min(num_blackout_buildings / 5.0, 1.0) * 0.5 # 최대 5개 건물 정전 시 0.5점
            severity_by_shortage = 0
            if current_total_demand > 1e-9:
                severity_by_shortage = min(total_affected_demand_blackout / current_total_demand, 1.0) * 0.5 # 피해량이 전체 수요의 100%면 0.5점
            
            blackout_severity = min(severity_by_count + severity_by_shortage, 1.0) # 최대 1.0
            
            problems.append({
                'type': 'blackout_buildings',
                'description': f"정전 발생: {num_blackout_buildings}개 건물 (총 피해수요: {total_affected_demand_blackout:.1f}). 상세: {', '.join(blackout_building_details)}",
                'severity': round(blackout_severity, 2),
                'entities': [b.name for b in power_system.blackout_buildings if hasattr(b, 'name')]
            })
            overall_severity_score = max(overall_severity_score, blackout_severity)


    # 3. 전반적인 수급 상황 및 전체 전력 부족
    total_demand = city.total_demand() 
    total_supply_capability = sum(b.base_supply for b in city.buildings if b.base_supply > 0 and not b.removed) # 기본 공급 능력의 합
    # 실제 현재 시점의 발전소들 current_supply 합 (태양광 등 변동성 반영)
    current_producer_output = sum(b.current_supply for b in city.buildings if b.base_supply > 0 and not b.removed and b.current_supply > 0)
    
    actual_total_supplied = power_system.calc_total_flow() 

    if total_demand > 1e-9:
        shortage_overall = total_demand - actual_total_supplied
        shortage_ratio = shortage_overall / total_demand if total_demand > 1e-9 else 0

        if shortage_overall > 1.0: # 유의미한 전체 부족
            severity = 0.0
            if shortage_ratio > 0.5: # 50% 이상 부족
                severity = 0.9 + (shortage_ratio - 0.5) # 0.9 ~ 1.4 (1.0으로 클리핑)
            elif shortage_ratio > 0.2: # 20% 이상 부족
                severity = 0.6 + (shortage_ratio - 0.2) * 1 # 0.6 ~ 0.9
            else: # 20% 미만 부족
                severity = 0.3 + shortage_ratio * 1.5 # 0.3 ~ 0.6
            
            severity = round(min(max(severity, 0.0), 1.0), 2)
            problems.append({
                'type': 'overall_shortage',
                'description': f"전체 전력 부족: 수요 {total_demand:.1f} 대비 실제 공급 {actual_total_supplied:.1f} (부족량 {shortage_overall:.1f}, 부족률 {(shortage_ratio*100):.1f}%)",
                'severity': severity,
                'entities': [] 
            })
            overall_severity_score = max(overall_severity_score, severity)
        
        # 공급 능력 부족 점검 (발전소의 기본 총합이 수요보다 아슬아슬한 경우)
        # current_producer_output은 태양광 등에 의해 변동하므로 total_supply_capability (기본 총합) 기준으로 판단
        supply_demand_margin = total_supply_capability - total_demand
        if supply_demand_margin < total_demand * 0.1: # 발전능력 마진이 총 수요의 10% 미만이면
            severity = 0.0
            if supply_demand_margin < 0: # 아예 부족하면
                severity = 0.8 + min(abs(supply_demand_margin) / total_demand, 1.0) * 0.2 # 0.8 ~ 1.0
            else: # 마진이 적으면
                severity = 0.4 + (1 - (supply_demand_margin / (total_demand * 0.1))) * 0.3 # 0.4 ~ 0.7
            
            severity = round(min(max(severity, 0.0), 1.0), 2)
            if severity > 0.4: # 유의미한 경우만 추가
                problems.append({
                    'type': 'low_supply_capacity_margin',
                    'description': f"공급 능력 부족 우려: 총 발전설비용량 {total_supply_capability:.1f} / 현재 총수요 {total_demand:.1f} (예비율 {(supply_demand_margin/total_demand*100  if total_demand > 1e-9 else 0):.1f}%)",
                    'severity': severity,
                    'entities': []
                })
                overall_severity_score = max(overall_severity_score, severity)

    # 4. 비효율 발전원 (간단 버전)
    # (base_supply 대비 current_supply가 현저히 낮은 발전소 - 외부요인 미고려)
    for b in city.buildings:
        if not b.removed and b.base_supply > 1e-9: # 발전소이고
             # 태양광 발전소는 시간대별 출력이 0일 수 있으므로 제외 (또는 building_type으로 구분)
            is_solar_producer = "solar" in b.building_type.lower() or "태양광" in b.get_type_str()

            if not is_solar_producer and b.current_supply < b.base_supply * 0.5: # 현재 출력이 기본의 50% 미만
                severity = 0.3 + (1 - (b.current_supply / (b.base_supply * 0.5))) * 0.3 # 0.3 ~ 0.6
                severity = round(min(max(severity, 0.0), 1.0), 2)
                problems.append({
                    'type': 'inefficient_producer',
                    'description': f"발전원 {b.name}: 출력 저하 의심 (기본 {b.base_supply:.1f}, 현재 {b.current_supply:.1f})",
                    'severity': severity,
                    'entities': [b.name]
                })
                overall_severity_score = max(overall_severity_score, severity)
                
    # 문제 목록을 심각도 순으로 정렬
    problems.sort(key=lambda p: p['severity'], reverse=True)

    # 종합적인 그리드 상태 요약 메시지 생성
    grid_summary = "분석 중..."
    if not problems and overall_severity_score < 0.1 : # 특별한 문제 없고 심각도 낮으면
        grid_summary = "현재 전력망 상태는 안정적입니다."
    elif overall_severity_score >= 0.9:
        grid_summary = "!! 매우 위험: 전력망에 심각한 문제가 다수 발생했습니다. 즉각적인 조치가 필요합니다."
    elif overall_severity_score >= 0.7:
        grid_summary = "! 위험: 전력망에 여러 문제가 감지되었습니다. 주의가 필요합니다."
    elif overall_severity_score >= 0.4:
        grid_summary = "주의: 전력망에 약간의 문제가 있습니다. 점검이 권장됩니다."
    else: # 심각도가 0.4 미만인 사소한 문제들만 있을 경우
        grid_summary = "양호: 전력망에 일부 경미한 사항이 있으나, 전반적으로 안정적입니다."
        if not problems: # 문제가 아예 없으면
             grid_summary = "최적: 현재 감지된 특이사항 없이 전력망이 안정적으로 운영 중입니다."


    return {'summary': grid_summary, 'problems': problems, 'overall_severity': round(overall_severity_score,2)}

def upgrade_critical_lines(simulator, budget_for_lines):
    """가장 사용률이 높은 송전선을 찾아 예산 내에서 용량을 증설하고 실제 소요 비용을 반환합니다."""
    city = simulator.city
    best_line_to_upgrade = None
    
    print(f"[DEBUG] 송전선 업그레이드 시작: 예산={budget_for_lines}")
    print(f"[DEBUG] 현재 송전선 개수: {len(city.lines) if hasattr(city, 'lines') else '알 수 없음'}")
    
    # 특정 송전선이 지정되었는지 확인
    if hasattr(simulator, 'target_line_for_upgrade') and simulator.target_line_for_upgrade:
        best_line_to_upgrade = simulator.target_line_for_upgrade
        # 사용 후 초기화
        simulator.target_line_for_upgrade = None
        
        if not best_line_to_upgrade.removed and best_line_to_upgrade.capacity > 1e-9:
            best_usage_rate = abs(best_line_to_upgrade.flow) / best_line_to_upgrade.capacity
            print(f"[DEBUG] 특정 송전선 {best_line_to_upgrade.u}-{best_line_to_upgrade.v} 업그레이드 지정됨 (사용률: {best_usage_rate*100:.1f}%)")
        else:
            best_line_to_upgrade = None
            print("[DEBUG] 지정된 송전선이 유효하지 않음 (제거되었거나 용량이 0)")
    
    # 지정된 송전선이 없거나 유효하지 않은 경우, 가장 사용률이 높은 송전선 찾기
    if best_line_to_upgrade is None:
        best_usage_rate = 0
        if hasattr(city, 'lines'):
            # 디버깅용: 모든 송전선의 사용률 출력
            print("[DEBUG] 현재 모든 송전선 상태:")
            for idx, line in enumerate(city.lines):
                if not line.removed and line.capacity > 1e-9:
                    usage_rate = (abs(line.flow) / line.capacity)
                    usage_pct = usage_rate * 100
                    print(f"  - 송전선 {line.u}-{line.v}: 흐름={line.flow:.2f}, 용량={line.capacity:.2f}, 사용률={usage_pct:.1f}%")
                    
                    # 가장 높은 사용률의 송전선 찾기
                    if usage_rate > best_usage_rate:
                        best_usage_rate = usage_rate
                        best_line_to_upgrade = line
    
    if not best_line_to_upgrade:
        print("[DEBUG] 업그레이드할 송전선이 없음.")
        return 0 # 업그레이드 대상 없음, 비용 0

    # 송전선 용량 증설량 결정 (예: 현재 용량의 20% 또는 최소 2단위)
    capacity_increase_amount = max(2.0, best_line_to_upgrade.capacity * 0.2) 
    
    # 비용 계산
    cost_per_unit_capacity = getattr(best_line_to_upgrade, 'cost', 0.5)
    if cost_per_unit_capacity < 1e-9: # 비용이 0에 가까우면 무료 업그레이드 방지 또는 기본 비용 설정
        cost_per_unit_capacity = 0.5 # 임의의 기본 단위 비용
        print(f"[DEBUG] 송전선 {best_line_to_upgrade.u}-{best_line_to_upgrade.v}의 cost가 0에 가까워 기본 단위 비용({cost_per_unit_capacity}) 적용")

    needed_cost_for_full_increase = capacity_increase_amount * cost_per_unit_capacity
    print(f"[DEBUG] 선택된 송전선 {best_line_to_upgrade.u}-{best_line_to_upgrade.v}: 현재 용량={best_line_to_upgrade.capacity:.2f}, 증설량={capacity_increase_amount:.2f}, 필요 비용={needed_cost_for_full_increase:.2f}, 사용률={best_usage_rate*100:.1f}%")
    
    actual_spent_cost = 0
    original_capacity = best_line_to_upgrade.capacity

    if needed_cost_for_full_increase <= budget_for_lines:
        best_line_to_upgrade.capacity += capacity_increase_amount
        actual_spent_cost = needed_cost_for_full_increase
        print(f"[DEBUG] 송전선 {best_line_to_upgrade.u}-{best_line_to_upgrade.v} 용량 증설 완료: {original_capacity:.1f} -> {best_line_to_upgrade.capacity:.1f} (비용: {actual_spent_cost:.1f})")
    elif budget_for_lines > cost_per_unit_capacity: # 최소 단위라도 증설 가능한 경우
        # 예산에 맞춰 가능한 만큼만 증설
        affordable_capacity_increase = budget_for_lines / cost_per_unit_capacity
        best_line_to_upgrade.capacity += affordable_capacity_increase
        actual_spent_cost = budget_for_lines # 예산 전부 사용
        print(f"[DEBUG] 송전선 {best_line_to_upgrade.u}-{best_line_to_upgrade.v} 용량 증설 완료: {original_capacity:.1f} -> {best_line_to_upgrade.capacity:.1f} (예산 내 최대, 비용: {actual_spent_cost:.1f})")
    else:
        print(f"[DEBUG] 송전선 {best_line_to_upgrade.u}-{best_line_to_upgrade.v} 증설 비용 부족 (필요 최소 비용: {cost_per_unit_capacity:.1f}, 가용 예산: {budget_for_lines:.1f})")
        return 0 # 비용 지출 없음

    # 타겟 송전선 정보를 시뮬레이터에 저장하여 UI에서 접근 가능하게 함
    simulator.last_upgraded_line = {
        'line': best_line_to_upgrade,
        'from': best_line_to_upgrade.u,
        'to': best_line_to_upgrade.v,
        'old_capacity': original_capacity,
        'new_capacity': best_line_to_upgrade.capacity,
        'usage_rate': best_usage_rate
    }

    return actual_spent_cost

def build_producer_in_needed_area(simulator, budget_for_producer):
    """전력 부족 지역 근처에 새 발전소를 건설하고 실제 소요 비용을 반환합니다."""
    city = simulator.city
    power_system = simulator.power_system
    
    PRODUCER_BASE_SUPPLY = 15.0 # 새로 건설될 발전소의 기본 공급량
    PRODUCER_COST = 100.0       # 발전소 건설 비용

    if budget_for_producer < PRODUCER_COST:
        print(f"[AI Upgrade] 발전소 건설 비용 부족 (필요: {PRODUCER_COST:.1f}, 예산: {budget_for_producer:.1f})")
        return 0 # 예산 부족, 비용 0

    target_building = None
    # 1순위: 정전 건물 중 가장 부족량이 큰 건물 근처
    if hasattr(power_system, 'blackout_buildings') and power_system.blackout_buildings:
        target_building = max(power_system.blackout_buildings, key=lambda b: getattr(b, 'shortage', 0), default=None)
    
    # 2순위: 정전 건물이 없다면, 수요가 있는 일반 소비자 건물 중 무작위 선택
    if not target_building:
        consumer_buildings = [b for b in city.buildings if not b.removed and b.base_supply < 0]
        if consumer_buildings:
            target_building = random.choice(consumer_buildings)
        else:
            print("[AI Upgrade] 발전소를 건설할 대상 소비자 건물을 찾을 수 없음.")
            return 0
            
    if not target_building:
        print("[AI Upgrade] 발전소 위치를 선정할 기준 건물을 찾지 못함.")
        return 0

    # 새 발전소 위치 결정 (대상 건물에서 약간 떨어진 곳)
    # TODO: 더 정교한 위치 선정 로직 (예: 빈 공간 찾기, 다른 건물과 겹치지 않도록 하기)
    # 현재는 간단히 x, y 좌표에 오프셋을 더함
    new_x = target_building.x + 60 + random.uniform(-10, 10) # 약간의 랜덤성 추가
    new_y = target_building.y + random.uniform(-10, 10)

    print(f"[AI Upgrade] {target_building.name} 근처 ({new_x:.1f}, {new_y:.1f})에 발전소 건설 시도...")
    
    # 새 건물 추가 시 building_type 명시
    new_producer = city.add_building(base_supply=PRODUCER_BASE_SUPPLY, x=new_x, y=new_y, building_type="producer")
    if new_producer:
        # add_building에서 name이 자동으로 idx 기반으로 생성되므로 별도 설정은 필요 없을 수 있음
        # 필요하다면 new_producer.name = f"AutoProducer_{new_producer.idx}" 등으로 설정
        print(f"[AI Upgrade] 새 발전소 {new_producer.name} (공급량: {PRODUCER_BASE_SUPPLY:.1f}) 건설 완료 (비용: {PRODUCER_COST:.1f})")
        return PRODUCER_COST
    else:
        print("[AI Upgrade] 알 수 없는 오류로 발전소 건설 실패.")
        return 0
