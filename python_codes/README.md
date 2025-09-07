# 전력 네트워크 시뮬레이터

이 프로젝트는 건물, 발전소, 송전선 등으로 구성된 전력 네트워크를 시뮬레이션하는 시스템입니다. 날씨, 온도, 경제적 요인 등 다양한 환경 요인을 고려한 실시간 시뮬레이션을 제공합니다.

## 주요 기능

- 건물, 발전소, 송전선으로 구성된 전력 네트워크 시뮬레이션
- 날씨, 온도, 미세먼지 등 환경 요인이 전력 수요에 미치는 영향 계산
- 태양광 발전량 계산 (태양 위치, 패널 각도, 날씨 고려)
- 배터리 충방전 시뮬레이션
- 전력 가격 변동 시뮬레이션
- 투자 수익률(ROI) 계산
- 랜덤 이벤트 시스템 (송전선 고장, 발전소 문제 등)
- 결과 분석 및 시각화
- 웹 인터페이스

## 설치 방법

1. 필요한 패키지 설치:
   ```
   pip install -r requirements.txt
   ```

2. 실행:
   ```
   python main.py
   ```

   웹 인터페이스로 실행:
   ```
   python main.py --web
   ```

   분석 리포트 생성:
   ```
   python main.py --analyze
   ```

   특정 시나리오만 실행:
   ```
   python main.py --scenario Scenario1
   ```

## 모듈 구조

- `modules/`: 시뮬레이션 핵심 모듈
  - `simulator.py`: 메인 시뮬레이션 클래스
  - `weather.py`: 날씨 시스템
  - `power.py`: 전력 계산 시스템
  - `event.py`: 이벤트 시스템
  - `economics.py`: 경제 모델
  - `analytics.py`: 시뮬레이션 결과 분석

- `web_interface/`: 웹 인터페이스
  - `app.py`: Flask 애플리케이션
  - `static/`: 정적 파일 (CSS, JavaScript)
  - `templates/`: HTML 템플릿

- `main.py`: 메인 실행 파일
- `city.py`: 도시 그래프 모델
- `data.py`: 기본 데이터 정의
- `algorithms.py`: 전력 흐름 계산 알고리즘
- `scenarios.json`: 시뮬레이션 시나리오 정의

## 시나리오 구성

시나리오는 `scenarios.json` 파일에 정의되어 있으며, 각 시나리오는 건물, 송전선, 예산, 수요 패턴 등을 포함합니다.

## 웹 인터페이스

웹 인터페이스는 다음 URL에서 접근할 수 있습니다:
- http://localhost:5000/

웹 인터페이스는 다음 기능을 제공합니다:
- 시뮬레이션 시작/정지/속도 조절
- 시나리오 선택 및 로드
- 전력 네트워크 시각화
- 실시간 상태 모니터링
- 경제 지표 표시

## LLM 분석 활성화

LLM 분석을 활성화하려면 다음 단계를 따르세요:
1. OpenAI API 키를 환경 변수로 설정: `export OPENAI_API_KEY=your_api_key`
2. `modules/analytics.py`에서 `self.use_llm_api = True`로 설정

## 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 