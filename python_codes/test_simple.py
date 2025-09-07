#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""간단한 발전소 테스트"""

import os
import json
from modules.simulator import Simulator

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

print("\n=== 발전소 테스트 ===")

# 태양광발전소 추가
solar = sim.city.add_solar_plant(100.0, 100, 100)
print(f"태양광발전소: idx={solar.idx}")
print(f"  solar_capacity: {solar.solar_capacity}")
print(f"  base_supply: {solar.base_supply}")
print(f"  current_supply (초기): {solar.current_supply}")

# 풍력발전소 추가
wind = sim.city.add_wind_plant(80.0, 200, 100)
print(f"\n풍력발전소: idx={wind.idx}")
print(f"  wind_capacity: {wind.wind_capacity}")
print(f"  base_supply: {wind.base_supply}")
print(f"  current_supply (초기): {wind.current_supply}")

# apply_demand_pattern 호출
print("\n=== apply_demand_pattern 호출 ===")
sim.apply_demand_pattern()

print(f"\n태양광발전소 current_supply (발전 후): {solar.current_supply}")
print(f"풍력발전소 current_supply (발전 후): {wind.current_supply}")

# 수소저장소 추가
hydrogen = sim.city.add_hydrogen_storage(100.0, 300, 100)
print(f"\n수소저장소: idx={hydrogen.idx}")
print(f"  hydrogen_storage: {hydrogen.hydrogen_storage}")
print(f"  hydrogen_level (초기): {hydrogen.hydrogen_level}")

# 태양광발전소와 수소저장소 연결
line = sim.city.add_line(solar.idx, hydrogen.idx, 50.0)
print(f"\n송전선 연결: {solar.idx} <-> {hydrogen.idx}")

# 수요처 추가
demand = sim.city.add_building(-50.0, 400, 100)
print(f"\n수요처: idx={demand.idx}, 수요량={demand.base_supply}")

# 다시 apply_demand_pattern 호출
print("\n=== apply_demand_pattern 다시 호출 (수소저장소 처리) ===")
sim.apply_demand_pattern()

print(f"\n수소저장소 hydrogen_level (처리 후): {hydrogen.hydrogen_level}")
print(f"수소저장소 current_supply: {hydrogen.current_supply}")

print("\n=== 테스트 완료 ===")