# Task Completion Checklist

## When Adding New Features
1. **Code Implementation**
   - Implement feature in appropriate module
   - Add Korean comments explaining logic
   - Update related UI components if needed

2. **Testing**
   - Run `python main.py` to test Pygame UI
   - Run `python main.py --web` to test Web UI (if applicable)
   - Test with multiple scenarios
   - Verify no Python errors or exceptions

3. **Integration Checks**
   - Ensure power flow calculations still work
   - Check that UI buttons respond correctly
   - Verify visual elements render properly
   - Test event handling

## When Modifying Power Plants
1. Update `models.py` for new plant types
2. Modify `PowerSystem.apply_demand_pattern()` in `modules/power.py`
3. Update UI buttons in `drawer_ui.py`
4. Add visual representation in `drawer_render.py`
5. Test power generation calculations

## When Fixing Bugs
1. Identify root cause in appropriate module
2. Apply fix with minimal side effects
3. Test all UI modes (Pygame and Web)
4. Verify scenario loading still works

## Final Validation
- [ ] Program runs without errors
- [ ] UI buttons are clickable and functional
- [ ] Power plants generate electricity correctly
- [ ] Visual elements display properly
- [ ] No overlapping UI elements
- [ ] Scenarios load successfully

## Common Issues to Check
- File paths work on Windows (use `os.path.join`)
- Korean text renders correctly
- Button click areas match visual buttons
- Dict vs Object attribute access handled properly