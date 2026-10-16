from app.sensors.touch import TouchSensor


def test_touch_message_queues_one_event():
    sensor = TouchSensor(port="COM3", debounce_seconds=0.4)

    sensor._handle_message("TOUCH", now=1.0)

    assert sensor.poll_touch() is True
    assert sensor.poll_touch() is False


def test_non_touch_message_is_ignored():
    sensor = TouchSensor(port="COM3")

    sensor._handle_message("READY", now=1.0)

    assert sensor.poll_touch() is False


def test_touch_messages_are_debounced():
    sensor = TouchSensor(port="COM3", debounce_seconds=0.4)

    sensor._handle_message("TOUCH", now=1.0)
    sensor._handle_message("TOUCH", now=1.2)
    sensor._handle_message("TOUCH", now=1.5)

    assert sensor.poll_touch() is True
    assert sensor.poll_touch() is True
    assert sensor.poll_touch() is False
