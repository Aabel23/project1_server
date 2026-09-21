from flexmix_machine.heartbeat import send_heartbeat


def test_heartbeat_failure_does_not_block_machine():
    heartbeat = {"status": "ready", "selling_available": True}
    assert send_heartbeat(lambda _: (_ for _ in ()).throw(OSError()), heartbeat) is False
    assert send_heartbeat(lambda _: {"ack": "ok"}, heartbeat) is True
