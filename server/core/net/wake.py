"""Đánh thức các poll đang chờ của cùng máy; không giữ hàng đợi lệnh."""

import math
import threading


class Wake:
    def __init__(self):
        # ponytail: một Condition kiểm tra lại mọi poll; tách theo máy nếu Q9 lớn.
        self._condition = threading.Condition()
        self._waiting = {}
        self._shutdown = 0
        self._stopping = False

    def wait(self, machine_id, timeout):
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout < 0:
            raise ValueError("Thời gian chờ phải hữu hạn và không âm")
        with self._condition:
            if self._stopping:
                return False
            state = self._waiting.setdefault(machine_id, [0, 0])
            state[1] += 1
            generation, shutdown = state[0], self._shutdown
            try:
                self._condition.wait_for(
                    lambda: state[0] != generation or self._shutdown != shutdown, timeout
                )
                return state[0] != generation and self._shutdown == shutdown
            finally:
                state[1] -= 1
                if not state[1]:
                    del self._waiting[machine_id]

    def notify(self, machine_id):
        with self._condition:
            state = self._waiting.get(machine_id)
            if state is not None:
                state[0] += 1
                self._condition.notify_all()

    def cancel_waiters(self):
        """Dừng cả poll hiện tại và poll tới muộn, cho tới khi resume."""
        with self._condition:
            self._stopping = True
            self._shutdown += 1
            self._condition.notify_all()

    def resume(self):
        """Mở lại wait trước khi listener khởi động; giữ generation hủy cũ."""
        with self._condition:
            self._stopping = False


wake = Wake()
