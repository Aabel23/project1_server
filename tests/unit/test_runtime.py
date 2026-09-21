from flexmix_machine.events import LocalOrderOutbox, EventUploadError
from flexmix_machine.runtime import LocalOrderRuntime, TicketNotClaimable

def test_local_ticket_atomic_claim_and_retry_sync(tmp_path):
    runtime = LocalOrderRuntime(tmp_path / "machine.db", LocalOrderOutbox(tmp_path / "outbox.json", machine_mid=1))
    runtime.create_ticket("T1", "tea", 100)
    try: runtime.claim_ticket("T1"); runtime.claim_ticket("T1")
    except TicketNotClaimable: pass
    else: raise AssertionError("second claim must fail")
    runtime.complete_ticket("T1")
    sent=[]
    def fail(_): raise OSError("offline")
    try: runtime.sync(fail)
    except EventUploadError: pass
    else: raise AssertionError("offline sync must fail")
    assert runtime.sync(lambda batch: (sent.append(batch) or {"ack":"ok","cursor_to":batch["cursor_to"]})) > 0
    assert runtime.get_ticket("T1")["status"] == "used"
