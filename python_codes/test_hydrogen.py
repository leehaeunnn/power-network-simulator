#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""수소저장소 연결 테스트"""

import sys
import os
import json
from modules.simulator import Simulator
from modules.economics import EconomicModel

def test_hydrogen_connection():
    """수소저장소 연결 테스트"""
    print("\n=== 수소저장소 연결 테스트 ===")
    
    # 시나리오 파일 로드
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scenario_file = os.path.join(script_dir, "scenarios.json")
    
    with open(scenario_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    scenario_list = data["scenarios"]
    
    # 시뮬레이터 생성
    sim = Simulator()
    sim.set_scenarios(scenario_list)
    sim.load_scenario(scenario_list[0])
    
    print("\n1. 발전소만 있는 수소저장소 (연결 없음)")
    # 수소저장소 추가 (연결 없음)
    hydrogen1 = sim.city.add_hydrogen_storage(100.0, 100, 100)
    print(f"   수소저장소 idx={hydrogen1.idx}")
    
    # apply_demand_pattern 호출하여 수소저장소 처리
    sim.apply_demand_pattern()
    # 전력 흐름 업데이트
    sim.update_flow(instant=True)
    print(f"   수소저장소 전력: {hydrogen1.current_supply}")
    print(f"   수소저장량: {hydrogen1.hydrogen_level:.2f}/{hydrogen1.hydrogen_storage:.2f}")
    
    print("\n2. 발전소와 연결된 수소저장소")
    # 태양광발전소 추가
    power_plant = sim.city.add_solar_plant(50.0, 200, 100)
    print(f"   태양광발전소 idx={power_plant.idx}, 용량={power_plant.solar_capacity}, base_supply={power_plant.base_supply}")
    
    # 수소저장소 추가
    hydrogen2 = sim.city.add_hydrogen_storage(100.0, 300, 100)
    print(f"   수소저장소 idx={hydrogen2.idx}")
    
    # 송전선으로 연결
    line = sim.city.add_line(power_plant.idx, hydrogen2.idx, 50.0)
    if line:
        print(f"   송전선 연결: {power_plant.idx} <-> {hydrogen2.idx}")
    else:
        print("   송전선 연결 실패!")
        return
    
    # 수요처 추가 (전체 시스템에 수요 생성)
    demand = sim.city.add_building(-30.0, 400, 100)
    print(f"   수요처 idx={demand.idx}, 수요량={demand.base_supply}")
    
    # 전력 흐름 업데이트 (잉여 전력 있음)
    print("\n3. 잉여 전력이 있을 때")
    print(f"   [발전 전] 태양광발전소 current_supply: {power_plant.current_supply}")
    print(f"   [발전 전] 태양광발전소 solar_capacity: {power_plant.solar_capacity}")
    print(f"   [발전 전] 태양광발전소 base_supply: {power_plant.base_supply}")
    # apply_demand_pattern 호출하여 수소저장소 처리
    sim.apply_demand_pattern()
    print(f"   [발전 후] 태양광발전소 current_supply: {power_plant.current_supply}")
    # 전력 흐름 업데이트
    sim.update_flow(instant=True)
    print(f"   발전소 전력: {power_plant.current_supply}")
    print(f"   수소저장소 전력: {hydrogen2.current_supply}")
    print(f"   수소저장량: {hydrogen2.hydrogen_level:.2f}/{hydrogen2.hydrogen_storage:.2f}")
    
    # 더 많은 수요 추가
    demand2 = sim.city.add_building(-40.0, 500, 100)
    print(f"\n4. 더 많은 수요 추가 (idx={demand2.idx}, 수요량={demand2.base_supply})")
    
    # 전력 흐름 업데이트 (전력 부족)
    sim.update_flow(instant=True)
    print(f"   발전소 전력: {power_plant.current_supply}")
    print(f"   수소저장소 전력: {hydrogen2.current_supply}")
    print(f"   수소저장량: {hydrogen2.hydrogen_level:.2f}/{hydrogen2.hydrogen_storage:.2f}")
    
    # 연결 확인
    print("\n5. 수소저장소 연결 상태 확인")
    connected_count = 0
    for line in sim.city.lines:
        if line.removed:
            continue
        if line.u == hydrogen2.idx or line.v == hydrogen2.idx:
            connected_count += 1
            if line.u == hydrogen2.idx:
                other_idx = line.v
            else:
                other_idx = line.u
            other_building = sim.city.buildings[other_idx]
            print(f"   연결된 건물: idx={other_idx}, supply={other_building.base_supply}")
    
    if connected_count == 0:
        print("   [경고] 수소저장소가 어떤 건물과도 연결되지 않음!")
    
    print("\n[완료] 수소저장소 테스트 완료")

if __name__ == "__main__":
    test_hydrogen_connection()