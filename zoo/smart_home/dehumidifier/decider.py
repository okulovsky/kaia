from .space import Space

def _should_stop(space: Space):
    turned_on_at = (space
                    .history_with_current(space.state, space.timestamp)
                    .take_while(lambda z: z.state)
                    .last()
                    .timestamp
                    )
    running_for = (space.timestamp.current_value - turned_on_at).total_seconds()/60
    if running_for > space.max_running_time.current_value:
        space.state_request.current_value = False
        space.state_request_reason.current_value = 'TimeLimit'
    elif space.humidity.current_value < space.low_humidity.current_value:
        space.state_request.current_value = False
        space.state_request_reason.current_value = 'Dehumidified'
    else:
        pass


def _should_start(space: Space):
    turned_off_at = (space
                     .history_with_current(space.state, space.timestamp)
                     .skip_while(lambda z: not z.state)
                     .select(lambda z: z.timestamp)
                     .first_or_default()
                     )
    if turned_off_at is None:
        space.state_request.current_value = True
        space.state_request_reason.current_value = 'Humid, Startup'
        return

    not_running_for = (space.timestamp.current_value - turned_off_at).total_seconds()/60
    if not_running_for < space.min_cooldown_time.current_value:
        space.state_request_reason.current_value = 'Cooldown'
    else:
        space.state_request.current_value = True
        space.state_request_reason.current_value = 'Humid'



def decider(space: Space):

    space.state_request.current_value = None
    space.state_request_reason.current_value = None

    if space.humidity.history.take(1).count()==0:
        return

    if space.humidifier_request.current_value is not None:
        space.state_request.current_value = space.humidifier_request.current_value
        space.state_request_reason.current_value = 'Requested'
        return

    if space.state.current_value:
        _should_stop(space)
        return

    if space.humidity.current_value > space.high_humidity.current_value:
        _should_start(space)
        return

