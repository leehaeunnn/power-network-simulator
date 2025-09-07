
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
    