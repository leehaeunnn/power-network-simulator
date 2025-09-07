# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Power Network Simulator (전력 네트워크 시뮬레이터) that simulates electrical power networks with environmental and economic factors. The system uses a graph-based model to represent buildings, power plants, and transmission lines, with real-time simulation of power flow, weather effects, and economic dynamics.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run with Pygame UI (default)
python main.py

# Run with web interface
python main.py --web

# Generate analysis report
python main.py --analyze

# Run specific scenario
python main.py --scenario Scenario1
```

## Architecture

The codebase follows a modular architecture with clear separation between simulation logic, UI, and data:

### Core Simulation Flow
1. **Entry Point**: `main.py` loads scenarios and routes to appropriate UI
2. **Simulator**: `modules/simulator.py` orchestrates all subsystems
3. **Network Model**: `city.py` defines graph-based power network (Buildings, PowerLines)
4. **Power Flow**: `algorithms.py` implements Edmonds-Karp max flow algorithm
5. **Subsystems**: Weather, Events, Economics modules update simulation state

### Key Integration Points
- **Scenario Loading**: All scenarios defined in `scenarios.json`
- **UI Interfaces**: Desktop (Pygame) in `drawer_*.py` files, Web (Flask) in `web_interface/`
- **Power Calculation**: Flow through network uses max-flow algorithm considering capacities
- **Time-based Updates**: Simulation advances in discrete time steps with demand patterns

### Module Dependencies
- `Simulator` class coordinates Weather, Power, Event, and Economics modules
- UI components observe simulation state but don't modify it directly
- All modules access shared `CityGraph` instance for network topology

## Development Guidelines

### Adding New Features
- New simulation behaviors: Extend appropriate module in `modules/`
- New UI elements: Desktop UI in `drawer_ui.py`, Web UI in `web_interface/templates/`
- New scenarios: Add to `scenarios.json` following existing structure

### Testing Changes
- No automated test suite exists; manual testing required
- Test with different scenarios to ensure compatibility
- Verify both UI modes (Pygame and Flask) work correctly

### LLM Analysis
To enable LLM-powered analysis:
1. Set environment variable: `export OPENAI_API_KEY=your_api_key`
2. Enable in code: Set `self.use_llm_api = True` in `modules/analytics.py`