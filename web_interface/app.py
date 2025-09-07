from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import threading
import time
import json
import os

# 앱과 소켓 전역 변수
app = None
socketio = None
simulator = None
update_thread = None
running = False

def create_app(sim):
    """Flask 앱 생성 및 설정"""
    global app, socketio, simulator
    simulator = sim
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # 정적 파일 디렉토리 생성
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
    
    # 템플릿 기본 파일 생성
    create_default_templates()
    
    # 라우트 설정
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/api/status')
    def get_status():
        return jsonify(get_simulator_status())
    
    @app.route('/api/scenarios')
    def get_scenarios():
        scenarios = [{"name": s["name"], "desc": s["desc"]} for s in simulator.scenarios]
        return jsonify(scenarios)
    
    @app.route('/api/load_scenario', methods=['POST'])
    def load_scenario():
        data = request.json
        scenario_name = data.get('scenario_name', '')
        
        # 해당 이름의 시나리오 찾기
        for s in simulator.scenarios:
            if s["name"] == scenario_name:
                simulator.load_scenario(s)
                return jsonify({"success": True, "message": f"시나리오 '{scenario_name}' 로드 완료"})
        
        return jsonify({"success": False, "message": f"시나리오 '{scenario_name}'를 찾을 수 없습니다"})
    
    @app.route('/api/control', methods=['POST'])
    def control_simulation():
        global running
        data = request.json
        command = data.get('command', '')
        
        if command == 'start':
            running = True
            if not update_thread.is_alive():
                start_update_thread()
            return jsonify({"success": True, "message": "시뮬레이션 시작"})
            
        elif command == 'pause':
            running = False
            return jsonify({"success": True, "message": "시뮬레이션 일시정지"})
            
        elif command == 'speed':
            speed = data.get('speed', 1.0)
            simulator.gameSpeed = float(speed) * 300.0  # 기본 속도 조정
            return jsonify({"success": True, "message": f"시뮬레이션 속도 {speed}x 설정"})
            
        return jsonify({"success": False, "message": "알 수 없는 명령"})
    
    @app.route('/api/buildings', methods=['GET'])
    def get_buildings():
        buildings = []
        for b in simulator.city.buildings:
            buildings.append({
                "id": b.idx,
                "x": b.x,
                "y": b.y,
                "type": b.get_type_str(),
                "supply": b.current_supply,
                "base_supply": b.base_supply,
                "solar_capacity": b.solar_capacity,
                "removed": b.removed,
                "blackout": b.blackout,
                "is_prosumer": b.is_prosumer,
                "battery_capacity": b.battery_capacity,
                "battery_charge": b.battery_charge
            })
        return jsonify(buildings)
    
    @app.route('/api/power_lines', methods=['GET'])
    def get_power_lines():
        lines = []
        for pl in simulator.city.lines:
            lines.append({
                "u": pl.u,
                "v": pl.v,
                "capacity": pl.capacity,
                "flow": pl.flow,
                "removed": pl.removed
            })
        return jsonify(lines)
    
    @app.route('/api/weather', methods=['GET'])
    def get_weather():
        return jsonify({
            "weather": simulator.weather_system.current_weather,
            "temperature": simulator.weather_system.current_temperature,
            "humidity": simulator.weather_system.humidity,
            "pm_level": simulator.weather_system.current_pm_level
        })
    
    @app.route('/api/economics', methods=['GET'])
    def get_economics():
        if simulator.economic_model:
            return jsonify(simulator.economic_model.get_economic_stats())
        return jsonify({"message": "경제 모델이 활성화되지 않았습니다."})
    
    @app.route('/api/report', methods=['GET'])
    def get_report():
        from modules.analytics import SimulationAnalytics
        analytics = SimulationAnalytics(simulator)
        return jsonify(analytics.generate_report())
    
    # 소켓 이벤트 설정
    @socketio.on('connect')
    def handle_connect():
        print("클라이언트 연결됨")
        socketio.emit('status_update', get_simulator_status())
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print("클라이언트 연결 해제")
    
    return app

def start_server(app, host='0.0.0.0', port=5000):
    """웹서버 시작"""
    global update_thread
    
    # 업데이트 스레드 시작
    update_thread = threading.Thread(target=update_simulation)
    update_thread.daemon = True
    update_thread.start()
    
    # 서버 시작
    socketio.run(app, host=host, port=port)

def update_simulation():
    """시뮬레이션 업데이트 스레드"""
    global running
    last_update = time.time()
    
    while True:
        try:
            if running:
                # 현재 시간과 경과 시간 계산
                current_time = time.time()
                elapsed_ms = (current_time - last_update) * 1000
                
                # 시뮬레이터 업데이트
                simulator.update_sim_time(elapsed_ms)
                simulator.apply_demand_pattern()
                simulator.update_events()
                simulator.update_flow(instant=True)
                
                # 상태 브로드캐스트
                socketio.emit('status_update', get_simulator_status())
                
                last_update = current_time
            else:
                last_update = time.time()
            
            # 업데이트 주기 (초당 5회 정도)
            time.sleep(0.2)
            
        except Exception as e:
            print(f"시뮬레이션 업데이트 오류: {str(e)}")
            time.sleep(1)

def get_simulator_status():
    """시뮬레이터 현재 상태 반환"""
    return {
        "time": simulator.simTime.isoformat(),
        "demand": abs(simulator.city.total_demand()),
        "supply": sum(b.current_supply for b in simulator.city.buildings 
                     if b.current_supply > 0 and not b.removed),
        "flow": simulator.calc_total_flow(),
        "blackout_count": len([b for b in simulator.city.buildings if b.blackout]),
        "weather": simulator.weather_system.current_weather,
        "temperature": simulator.weather_system.current_temperature,
        "money": simulator.money,
        "budget": simulator.budget,
        "event_count": simulator.event_count,
        "running": running,
        "speed": simulator.gameSpeed / 300.0
    }

def create_default_templates():
    """기본 템플릿 파일 생성"""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    static_dir = os.path.join(os.path.dirname(__file__), 'static')
    
    # index.html 파일
    index_html = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>전력 네트워크 시뮬레이터</title>
        <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
        <script src="https://cdn.socket.io/4.4.1/socket.io.min.js"></script>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>전력 네트워크 시뮬레이터</h1>
                <div class="controls">
                    <button id="start-btn">시작</button>
                    <button id="pause-btn">일시정지</button>
                    <select id="speed-selector">
                        <option value="0.5">0.5x 속도</option>
                        <option value="1" selected>1x 속도</option>
                        <option value="2">2x 속도</option>
                        <option value="5">5x 속도</option>
                        <option value="10">10x 속도</option>
                    </select>
                </div>
            </header>
            
            <main>
                <div class="dashboard">
                    <div class="status-card">
                        <h2>시뮬레이션 상태</h2>
                        <p>시간: <span id="sim-time">-</span></p>
                        <p>날씨: <span id="weather">-</span></p>
                        <p>온도: <span id="temperature">-</span>°C</p>
                        <p>이벤트 수: <span id="event-count">-</span></p>
                    </div>
                    
                    <div class="status-card">
                        <h2>전력 네트워크</h2>
                        <p>수요: <span id="demand">-</span></p>
                        <p>공급: <span id="supply">-</span></p>
                        <p>유량: <span id="flow">-</span></p>
                        <p>정전 건물: <span id="blackout-count">-</span></p>
                    </div>
                    
                    <div class="status-card">
                        <h2>경제 지표</h2>
                        <p>예산: <span id="budget">-</span></p>
                        <p>자금: <span id="money">-</span></p>
                        <p>전기 가격: <span id="electricity-price">-</span></p>
                    </div>
                </div>
                
                <div class="network-view">
                    <h2>네트워크 시각화</h2>
                    <div id="network-container">
                        <canvas id="network-canvas" width="800" height="600"></canvas>
                    </div>
                </div>
                
                <div class="scenario-selector">
                    <h2>시나리오</h2>
                    <select id="scenario-list"></select>
                    <button id="load-scenario-btn">시나리오 로드</button>
                </div>
            </main>
        </div>
        
        <script src="{{ url_for('static', filename='app.js') }}"></script>
    </body>
    </html>
    """
    
    # app.js 파일
    app_js = """
    // 소켓 연결
    const socket = io();
    
    // DOM 요소 참조
    const startBtn = document.getElementById('start-btn');
    const pauseBtn = document.getElementById('pause-btn');
    const speedSelector = document.getElementById('speed-selector');
    const scenarioList = document.getElementById('scenario-list');
    const loadScenarioBtn = document.getElementById('load-scenario-btn');
    const canvas = document.getElementById('network-canvas');
    const ctx = canvas.getContext('2d');
    
    // 상태 업데이트 요소
    const simTimeEl = document.getElementById('sim-time');
    const weatherEl = document.getElementById('weather');
    const temperatureEl = document.getElementById('temperature');
    const eventCountEl = document.getElementById('event-count');
    const demandEl = document.getElementById('demand');
    const supplyEl = document.getElementById('supply');
    const flowEl = document.getElementById('flow');
    const blackoutCountEl = document.getElementById('blackout-count');
    const budgetEl = document.getElementById('budget');
    const moneyEl = document.getElementById('money');
    const electricityPriceEl = document.getElementById('electricity-price');
    
    // 시뮬레이션 데이터
    let buildings = [];
    let powerLines = [];
    let economicData = {};
    
    // 이벤트 리스너 설정
    startBtn.addEventListener('click', () => {
        fetch('/api/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'start' })
        });
    });
    
    pauseBtn.addEventListener('click', () => {
        fetch('/api/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'pause' })
        });
    });
    
    speedSelector.addEventListener('change', () => {
        const speed = speedSelector.value;
        fetch('/api/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'speed', speed: speed })
        });
    });
    
    loadScenarioBtn.addEventListener('click', () => {
        const scenarioName = scenarioList.value;
        fetch('/api/load_scenario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario_name: scenarioName })
        }).then(res => res.json())
          .then(data => {
              if (data.success) {
                  alert(data.message);
                  fetchNetworkData();
              } else {
                  alert("오류: " + data.message);
              }
          });
    });
    
    // 소켓 이벤트 핸들러
    socket.on('status_update', (data) => {
        updateDashboard(data);
    });
    
    // 시나리오 목록 가져오기
    function fetchScenarios() {
        fetch('/api/scenarios')
            .then(res => res.json())
            .then(scenarios => {
                scenarioList.innerHTML = '';
                scenarios.forEach(scenario => {
                    const option = document.createElement('option');
                    option.value = scenario.name;
                    option.textContent = `${scenario.name} - ${scenario.desc}`;
                    scenarioList.appendChild(option);
                });
            });
    }
    
    // 네트워크 데이터 가져오기
    function fetchNetworkData() {
        Promise.all([
            fetch('/api/buildings').then(res => res.json()),
            fetch('/api/power_lines').then(res => res.json()),
            fetch('/api/economics').then(res => res.json())
        ]).then(([bldgs, lines, econ]) => {
            buildings = bldgs;
            powerLines = lines;
            economicData = econ;
            drawNetwork();
        });
    }
    
    // 대시보드 업데이트
    function updateDashboard(data) {
        simTimeEl.textContent = new Date(data.time).toLocaleString();
        weatherEl.textContent = data.weather;
        temperatureEl.textContent = data.temperature.toFixed(1);
        eventCountEl.textContent = data.event_count;
        demandEl.textContent = data.demand.toFixed(1);
        supplyEl.textContent = data.supply.toFixed(1);
        flowEl.textContent = data.flow.toFixed(1);
        blackoutCountEl.textContent = data.blackout_count;
        budgetEl.textContent = data.budget.toFixed(1);
        moneyEl.textContent = data.money.toFixed(1);
        
        // 주기적으로 네트워크 데이터 업데이트
        fetchNetworkData();
    }
    
    // 네트워크 그리기
    function drawNetwork() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 송전선 그리기
        powerLines.forEach(line => {
            if (line.removed) return;
            
            const b1 = buildings.find(b => b.id === line.u);
            const b2 = buildings.find(b => b.id === line.v);
            
            if (!b1 || !b2 || b1.removed || b2.removed) return;
            
            // 좌표 변환
            const x1 = b1.x * 0.8 + 50;
            const y1 = b1.y * 0.8 + 50;
            const x2 = b2.x * 0.8 + 50;
            const y2 = b2.y * 0.8 + 50;
            
            // 선 두께는 용량에 비례
            const lineWidth = Math.max(1, Math.min(8, line.capacity / 2));
            
            // 흐름에 따른 색상
            let color;
            const utilization = Math.abs(line.flow) / line.capacity;
            if (utilization > 0.9) {
                color = 'red';  // 과부하
            } else if (utilization > 0.7) {
                color = 'orange';  // 높은 부하
            } else if (Math.abs(line.flow) > 0.1) {
                color = 'blue';  // 정상 흐름
            } else {
                color = 'gray';  // 미미한 흐름
            }
            
            // 송전선 그리기
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.strokeStyle = color;
            ctx.lineWidth = lineWidth;
            ctx.stroke();
            
            // 흐름 방향 화살표
            if (Math.abs(line.flow) > 0.1) {
                const arrowSize = 8;
                const angle = Math.atan2(y2 - y1, x2 - x1);
                const midX = (x1 + x2) / 2;
                const midY = (y1 + y2) / 2;
                
                ctx.beginPath();
                if (line.flow > 0) {  // u -> v 방향
                    ctx.moveTo(midX, midY);
                    ctx.lineTo(midX - arrowSize * Math.cos(angle - Math.PI/6), midY - arrowSize * Math.sin(angle - Math.PI/6));
                    ctx.lineTo(midX - arrowSize * Math.cos(angle + Math.PI/6), midY - arrowSize * Math.sin(angle + Math.PI/6));
                } else {  // v -> u 방향
                    ctx.moveTo(midX, midY);
                    ctx.lineTo(midX + arrowSize * Math.cos(angle - Math.PI/6), midY + arrowSize * Math.sin(angle - Math.PI/6));
                    ctx.lineTo(midX + arrowSize * Math.cos(angle + Math.PI/6), midY + arrowSize * Math.sin(angle + Math.PI/6));
                }
                ctx.fillStyle = color;
                ctx.fill();
            }
        });
        
        // 건물 그리기
        buildings.forEach(b => {
            if (b.removed) return;
            
            // 좌표 변환
            const x = b.x * 0.8 + 50;
            const y = b.y * 0.8 + 50;
            
            // 건물 유형에 따른 색상
            let color;
            if (b.blackout) {
                color = 'black';  // 정전
            } else if (b.supply > 0) {
                color = 'green';  // 발전소
            } else if (b.is_prosumer) {
                color = 'purple';  // 프로슈머
            } else if (b.supply < 0) {
                color = 'red';  // 수요 건물
            } else {
                color = 'gray';  // 중립 건물
            }
            
            // 건물 크기는 공급/수요량에 비례
            const size = Math.max(8, Math.min(20, Math.abs(b.supply) * 2 + 8));
            
            // 건물 그리기
            ctx.beginPath();
            ctx.arc(x, y, size, 0, Math.PI * 2);
            ctx.fillStyle = color;
            ctx.fill();
            
            // 태양광 설비 표시
            if (b.solar_capacity > 0) {
                ctx.beginPath();
                ctx.arc(x, y, size + 4, 0, Math.PI * 2);
                ctx.strokeStyle = 'yellow';
                ctx.lineWidth = 2;
                ctx.stroke();
            }
            
            // 배터리 표시
            if (b.battery_capacity > 0) {
                const batteryHeight = 6;
                const batteryWidth = 10;
                const fillRatio = b.battery_charge / b.battery_capacity;
                
                ctx.fillStyle = 'darkgreen';
                ctx.fillRect(x - batteryWidth/2, y + size + 4, batteryWidth, batteryHeight);
                
                ctx.fillStyle = 'lightgreen';
                ctx.fillRect(
                    x - batteryWidth/2, 
                    y + size + 4 + batteryHeight * (1 - fillRatio), 
                    batteryWidth, 
                    batteryHeight * fillRatio
                );
            }
            
            // 건물 ID 표시
            ctx.fillStyle = 'white';
            ctx.font = '10px Arial';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(b.id.toString(), x, y);
        });
    }
    
    // 초기 데이터 로드
    fetchScenarios();
    fetch('/api/status')
        .then(res => res.json())
        .then(data => updateDashboard(data));
    """
    
    # style.css 파일
    style_css = """
    * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
        font-family: Arial, sans-serif;
    }
    
    body {
        background-color: #f5f5f5;
    }
    
    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    
    header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid #ddd;
    }
    
    h1 {
        color: #333;
    }
    
    .controls {
        display: flex;
        gap: 10px;
    }
    
    button {
        padding: 8px 16px;
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    
    button:hover {
        background-color: #45a049;
    }
    
    select {
        padding: 8px;
        border-radius: 4px;
        border: 1px solid #ddd;
    }
    
    .dashboard {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 20px;
        margin-bottom: 20px;
    }
    
    .status-card {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .status-card h2 {
        color: #333;
        margin-bottom: 15px;
        padding-bottom: 5px;
        border-bottom: 1px solid #eee;
    }
    
    .status-card p {
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
    }
    
    .network-view {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .network-view h2 {
        color: #333;
        margin-bottom: 15px;
    }
    
    #network-container {
        border: 1px solid #ddd;
        overflow: hidden;
    }
    
    .scenario-selector {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .scenario-selector h2 {
        color: #333;
        margin-bottom: 15px;
    }
    
    #scenario-list {
        width: 100%;
        margin-bottom: 10px;
    }
    """
    
    # 파일 생성
    with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
        
    with open(os.path.join(static_dir, 'app.js'), 'w', encoding='utf-8') as f:
        f.write(app_js)
        
    with open(os.path.join(static_dir, 'style.css'), 'w', encoding='utf-8') as f:
        f.write(style_css) 