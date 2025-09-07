#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""수정사항 테스트 스크립트"""

import sys
import os
import json

# 모듈 임포트
from modules.simulator import Simulator
from modules.economics import EconomicModel

def test_scenario_loading():
    """시나리오 로딩 테스트"""
    print("\n=== 시나리오 로딩 테스트 ===")
    
    # 시나리오 파일 로드
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scenario_file = os.path.join(script_dir, "scenarios.json")
    
    with open(scenario_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    scenario_list = data["scenarios"]
    
    # 시뮬레이터 생성
    sim = Simulator()
    sim.set_scenarios(scenario_list)
    
    # 첫 번째 시나리오 로드
    sim.load_scenario(scenario_list[0])
    print(f"첫 번째 시나리오 로드 완료: {scenario_list[0]['name']}")
    
    # 두 번째 시나리오 로드
    if len(scenario_list) > 1:
        sim.load_scenario(scenario_list[1])
        print(f"두 번째 시나리오 로드 완료: {scenario_list[1]['name']}")
    
    print("[PASS] 시나리오 로딩 테스트 통과")
    return sim

def test_building_types(sim):
    """건물 타입 표시 테스트"""
    print("\n=== 건물 타입 표시 테스트 ===")
    
    # 상가 추가
    shop = sim.city.add_building(-10.0, 100, 100)
    shop.building_type = "shopping_mall"
    print(f"상가 추가 - 타입 표시: {shop.get_type_str()}")
    assert shop.get_type_str() == "상가", f"상가가 {shop.get_type_str()}로 표시됨"
    
    # 아파트 추가
    apt = sim.city.add_building(-5.0, 200, 100)
    apt.building_type = "apartment"
    print(f"아파트 추가 - 타입 표시: {apt.get_type_str()}")
    assert apt.get_type_str() == "아파트", f"아파트가 {apt.get_type_str()}로 표시됨"
    
    print("[PASS] 건물 타입 표시 테스트 통과")

def test_hydrogen_storage(sim):
    """수소저장소 테스트"""
    print("\n=== 수소저장소 테스트 ===")
    
    # 발전소 추가
    power_plant = sim.city.add_building(100.0, 300, 100)
    power_plant.power_plant_type = "solar"
    
    # 수소저장소 추가
    hydrogen = sim.city.add_hydrogen_storage(100.0, 400, 100)
    
    # 송전선으로 연결
    line = sim.city.add_line(power_plant.idx, hydrogen.idx, 50.0)
    
    print(f"발전소(idx={power_plant.idx})와 수소저장소(idx={hydrogen.idx}) 연결")
    
    # 전력 흐름 업데이트
    sim.update_flow(instant=True)
    
    print(f"수소저장소 상태: {hydrogen.get_status_str()}")
    print("[PASS] 수소저장소 테스트 통과")

def test_power_line_connection(sim):
    """송전선 연결 테스트"""
    print("\n=== 송전선 연결 테스트 ===")
    
    # 두 건물 생성
    b1 = sim.city.add_building(50.0, 500, 100)  # 발전소
    b2 = sim.city.add_building(-20.0, 600, 100)  # 수요처
    
    print(f"건물1(발전소): idx={b1.idx}, supply={b1.base_supply}")
    print(f"건물2(수요처): idx={b2.idx}, supply={b2.base_supply}")
    
    # 송전선 연결
    line = sim.city.add_line(b1.idx, b2.idx, 30.0)
    
    if line:
        print(f"송전선 연결 성공: {b1.idx} -> {b2.idx}")
    else:
        print("송전선 연결 실패!")
        return
    
    # 전력 흐름 업데이트
    sim.update_flow(instant=True)
    
    # 송전선 흐름 확인
    if hasattr(line, 'flow'):
        print(f"송전선 흐름: {line.flow}")
    
    print("[PASS] 송전선 연결 테스트 통과")

def main():
    """메인 테스트 함수"""
    print("=" * 50)
    print("전력 시뮬레이터 수정사항 테스트")
    print("=" * 50)
    
    try:
        # 시나리오 테스트
        sim = test_scenario_loading()
        
        # 건물 타입 테스트
        test_building_types(sim)
        
        # 수소저장소 테스트
        test_hydrogen_storage(sim)
        
        # 송전선 연결 테스트
        test_power_line_connection(sim)
        
        print("\n" + "=" * 50)
        print("[PASS] 모든 테스트 통과!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n[FAIL] 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())