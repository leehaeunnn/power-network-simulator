# Project Overview

## Project Purpose
Power Network Simulator (전력 네트워크 시뮬레이터) - A comprehensive simulation system for electrical power networks with environmental and economic factors.

## Tech Stack
- **Language**: Python 3.x
- **UI Framework**: Pygame 2.1.2 (Desktop), Flask 2.0.2 + SocketIO (Web)
- **Data Visualization**: Matplotlib 3.5.1
- **Numerical Computing**: NumPy 1.22.2
- **AI Integration**: OpenAI API 0.27.0 (optional)

## Core Features
- Graph-based power network modeling (buildings, power plants, transmission lines)
- Real-time power flow simulation using Edmonds-Karp max flow algorithm
- Environmental factor simulation (weather, temperature, PM levels)
- Multiple power plant types: Wind, Solar, Hydro, Thermal, Hydrogen Storage
- Battery charge/discharge simulation
- Economic modeling with ROI calculations
- Random event system
- Scenario-based simulation

## Architecture
- **Entry Point**: `main.py`
- **Core Simulation**: `modules/simulator.py` orchestrates subsystems
- **Network Model**: `city.py` (CityGraph class)
- **Power Flow**: `algorithms.py` (max flow implementation)
- **UI Layer**: `drawer_*.py` (Pygame), `web_interface/` (Flask)
- **Data**: `scenarios.json` defines simulation scenarios

## Recent Additions
- Separate power plant types (Wind, Solar, Hydro) with unique characteristics
- Hydrogen energy storage system with electrolysis and fuel cell efficiency
- Visual differentiation for each power plant type
- Power plant selection UI with individual buttons