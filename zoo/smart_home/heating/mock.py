from .space import Space

def mock_heating(space: Space):
    if space.temperature_setpoint.length() == 0:
        space.temperature_setpoint.current_value = 20
        space.temperature_on_sensor.current_value = 21
    else:
        if space.temperature_setpoint_command.last_value is not None:
            space.temperature_setpoint.current_value = space.temperature_setpoint_command.last_value/100
        else:
            space.temperature_setpoint.current_value = space.temperature_setpoint.last_value

        delta_in_minutes = (space.timestamp.current_value - space.timestamp.last_value).total_seconds()/60

        if space.valve_position.last_value > 50:
            space.temperature_on_sensor.current_value = space.temperature_on_sensor.last_value + 1*delta_in_minutes
        else:
            space.temperature_on_sensor.current_value = space.temperature_on_sensor.last_value - 1*delta_in_minutes

    space.temperature_on_thermostat.current_value = int(space.temperature_on_sensor.current_value)
    if space.temperature_on_thermostat.current_value < space.temperature_setpoint.current_value:
        space.valve_position.current_value = 100
    else:
        space.valve_position.current_value = 0


def mock_acutator(space: Space):
    space.temperature_setpoint_feedback.current_value = space.temperature_setpoint_command.current_value




