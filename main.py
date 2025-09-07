import sys
import os
import json
import argparse
from modules.simulator import Simulator
from modules.analytics import SimulationAnalytics
from modules.economics import EconomicModel
from data import *
from algorithms import *
from utils import *

# UI 임포트를 조건부로 처리
def main():
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description='전력 네트워크 시뮬레이터')
    parser.add_argument('--analyze', action='store_true', help='시뮬레이션 결과 분석')
    parser.add_argument('--scenario', type=str, help='특정 시나리오 이름')
    args = parser.parse_args()

    # 시나리오 JSON 로드
    # 현재 스크립트의 디렉토리를 기준으로 경로 설정
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scenario_file = os.path.join(script_dir, "scenarios.json")
    try:
        with open(scenario_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[에러] 시나리오 파일({scenario_file})을 찾을 수 없습니다.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"[에러] 시나리오 파일({scenario_file})의 형식이 잘못되었습니다 (JSON 오류).")
        sys.exit(1)
    except Exception as e:
        print(f"[에러] 시나리오 파일({scenario_file}) 로드 중 예상치 못한 오류 발생: {e}") 
        sys.exit(1)

    # "scenarios" 키 존재 여부 및 리스트 타입 확인 강화
    if "scenarios" not in data or not isinstance(data["scenarios"], list):
        print(f"[에러] 시나리오 파일({scenario_file})에 'scenarios' 리스트가 없거나 형식이 잘못되었습니다.")
        sys.exit(1)
        
    scenario_list = data["scenarios"]
    if not scenario_list:
        # scenarios 키는 있지만 리스트가 비어있는 경우
        print(f"[에러] 시나리오 파일({scenario_file})에 정의된 시나리오가 없습니다.")
        sys.exit(1)
    
    # 특정 시나리오 이름이 주어진 경우 해당 시나리오만 필터링
    if args.scenario:
        scenario_list = [s for s in scenario_list if s["name"] == args.scenario]
        if not scenario_list:
            print(f"[에러] '{args.scenario}' 시나리오를 찾을 수 없습니다.")
            sys.exit(1)
    
    # 시뮬레이터 생성
    sim = Simulator()
    sim.gameSpeed = 6000.0 # 기존 300.0에서 20배 빠르게 설정 (1초당 100시간)
    sim.set_scenarios(scenario_list)
    
    # 경제 모델 연결
    econ_model = EconomicModel(sim)
    sim.set_economic_model(econ_model)
    
    # 초기에 첫 시나리오 불러오기
    sim.load_scenario(scenario_list[0])
    
    # Pygame UI 사용
    # Pygame UI 관련 모듈을 여기서 import
    from uis import ParticleSystem, Button, ContextMenu
    from drawer_base import Drawer
    
    # Drawer 생성 + 실행
    drawer = Drawer(sim)
    drawer.run()
    
    # 시뮬레이션 결과 분석 (--analyze 옵션이 있는 경우)
    if args.analyze:
        analytics = SimulationAnalytics(sim)
        results = analytics.generate_report()
        print("\n===== 시뮬레이션 분석 결과 =====")
        for key, value in results.items():
            print(f"{key}: {value}")
        
        # LLM 분석 결과 출력 (옵션)
        if hasattr(analytics, 'get_llm_analysis'):
            print("\n===== LLM 분석 =====")
            print(analytics.get_llm_analysis())

if __name__=="__main__":
    main()
