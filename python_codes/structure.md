# 프로젝트 구조 및 주요 모듈 설명

## 1. 코어 모듈 (`core/`)

### `city_graph.py`
*   **`CityGraph` 클래스**: 도시 전체의 전력 네트워크를 그래프 형태로 표현하고 관리. 건물(`Building`) 노드와 송전선(`PowerLine`) 엣지로 구성.
    *   `add_building(building_data)`: 그래프에 건물 노드 추가.
    *   `add_line(line_data)`: 그래프에 송전선 엣지 추가.
    *   `remove_building(building_idx)`: 건물 노드 제거.
    *   `remove_line(line_idx)`: 송전선 엣지 제거.
    *   `get_building(building_idx)`: 특정 건물 객체 반환.
    *   `get_line(line_idx)`: 특정 송전선 객체 반환.
    *   `upgrade_line_capacity(line_idx, additional_capacity)`: 송전선 용량 증설.

### `buildings.py`
*   **`Building` 클래스**: 전력망의 기본 단위 (발전, 소비, 프로슈머 등).
    *   `update_demand()`: 현재 시간 및 기상 조건에 따라 전력 수요량(`current_demand`) 갱신.
    *   `update_solar_generation()`: 태양광 발전량(`current_supply`) 갱신.
    *   `update_battery()`: 배터리 충방전 로직 수행 및 `battery_charge` 갱신.
    *   `upgrade_battery_capacity(additional_kwh)`: 배터리 용량 증설.

### `power_lines.py`
*   **`PowerLine` 클래스**: 두 건물 노드를 연결하는 송전선. `capacity`, `current_flow` 등의 속성 관리.

## 2. 시뮬레이션 제어 (`simulator.py`)

*   **`Simulator` 클래스**: 시뮬레이션 전체 흐름 제어.
    *   `__init__(scenario_path)`: 시나리오 로드 및 시뮬레이터 초기화.
    *   `load_scenario(file_path)`: JSON 시나리오 파일 로드 및 환경 설정.
    *   `run_simulation()`: 메인 시뮬레이션 루프 실행.
    *   `advance_time()`: 시뮬레이션 시간(`current_time`)을 `time_step`만큼 증가.
    *   `get_state()`: 현재 시뮬레이션 상태 반환 (UI용).

## 3. 동적 환경 모듈 (`modules/`)

### `weather.py`
*   **`WeatherSystem` 클래스**: 기상 조건(기온, 습도, 일사량 등) 생성 및 업데이트.
    *   `update_weather(current_time)`: 현재 시간에 맞는 기상 데이터 생성/갱신.
    *   `get_current_weather()`: 현재 기상 정보 반환.

### `event.py`
*   **`EventSystem` 클래스**: 예측 불가능한 이벤트(송전선 고장, 발전소 출력 변동 등) 관리 및 발생.
    *   `trigger_event(city_graph, current_time)`: 조건/확률에 따라 이벤트 발생 및 시스템 상태 변경.

### `economics.py` (기본 구조)
*   **`EconomicModel` 클래스**: 에너지 가격, 운영 비용, 투자 수익 등 경제적 측면 시뮬레이션 (확장 예정).
    *   `get_current_electricity_price()`: 현재 전력 가격 반환 (가상).
    *   `evaluate_investment()`: 투자 경제성 평가 (가상).

### `power_system.py`
*   **`PowerSystem` 클래스**: 전력 조류 계산 및 분배 담당.
    *   `calculate_power_flow(city_graph)`: Edmonds-Karp 알고리즘 등을 이용해 전력 흐름 계산, `PowerLine`의 `current_flow` 및 `Building`의 `blackout` 상태 업데이트.
    *   `_run_edmonds_karp()`: Edmonds-Karp 알고리즘 핵심 로직.
    *   `_find_augmenting_path_bfs()`: BFS를 이용한 증가 경로 탐색.

### `intelligent_agent.py`
*   **`IntelligentAgent` 클래스**: AI 기반 그리드 관리 및 의사결정.
    *   `make_decision(city_graph, budget)`: 그리드 상태 분석 후 최적화 전략 결정 및 실행.
    *   `diagnose_grid_state(city_graph)`: 전력망 문제점(과부하, 정전 등) 진단 및 상태 점수 계산.
    *   `upgrade_power_line_capacity()`: 송전선 용량 증설 전략 실행.
    *   `build_new_power_plant()`: 신규 발전소 건설 전략 실행.
    *   `optimize_battery_storage()`: 배터리 시스템 최적화 전략 실행.

### `analytics.py`
*   **`SimulationAnalytics` 클래스**: 시뮬레이션 데이터 로깅 및 분석.
    *   `log_data(timestamp, data_dict)`: 주요 데이터 기록.
    *   `get_summary_statistics()`: 통계 요약 정보 반환.

### `data_management.py` (가정)
*   `load_static_data(file_path)`: `data.py` 등에서 정적 데이터 로드.
*   `load_patterns(file_path)`: 수요/공급 패턴 데이터 로드.

## 4. 사용자 인터페이스 (`ui/`) - 가정

### `gui_pygame.py` (가정)
*   Pygame 기반 로컬 GUI 구현.
    *   `render_state(city_graph, simulator_state)`: 현재 상태 시각화.

### `web_flask.py` (가정)
*   Flask/SocketIO 기반 웹 인터페이스 구현.

## 5. 데이터 및 설정

*   `scenarios.json`: 시뮬레이션 시나리오 정의 파일.
*   `data.py` (또는 `config/data.py`): 기본 계수, 패턴, 설정값 등 정적 데이터 정의.

---

**주요 상호작용:**
- `Simulator`가 메인 루프를 돌며 각 모듈의 `update` 또는 관련 메서드 호출.
- `IntelligentAgent`는 `CityGraph`를 분석하고, `Simulator`의 예산을 사용하여 `CityGraph` 변경.
- `PowerSystem`은 `CityGraph` 정보를 기반으로 전력 흐름 계산 후 `Building`, `PowerLine` 상태 변경.
- 각 `Building`은 `WeatherSystem`의 영향을 받아 수요/공급 변경. 