# Code Style and Conventions

## Language
- Python 3.x
- Korean comments and UI text (한글 주석 및 UI 텍스트)
- English variable and function names

## Naming Conventions
- **Classes**: PascalCase (e.g., `PowerSystem`, `WindPowerPlant`)
- **Functions/Methods**: snake_case (e.g., `calculate_output`, `update_flow`)
- **Variables**: snake_case (e.g., `wind_speed`, `solar_capacity`)
- **Constants**: UPPER_SNAKE_CASE (rarely used in this project)

## Code Structure
- Classes for major components (Building, PowerLine, CityGraph)
- Inheritance for power plant types (WindPowerPlant extends Building)
- Modular architecture with separate files for different systems

## Documentation
- Korean docstrings for methods ("""메서드 설명""")
- Inline comments in Korean explaining logic
- Type hints not consistently used

## UI Conventions
- Button dictionaries with structure: `{"text": str, "x": int, "y": int, "width": int, "height": int, "action": callable}`
- Color tuples as RGB or RGBA
- Pygame event handling pattern with event loop

## File Organization
- `modules/` directory for simulation subsystems
- `web_interface/` for Flask components
- `drawer_*.py` files for Pygame UI components
- Single `scenarios.json` for all scenario definitions

## Common Patterns
- Lambda functions for button actions
- Dictionary-based configuration
- Event-driven UI updates
- Graph-based network representation