import unittest

from queue import Queue
from threading import Thread
import time

from lib.time.busy_wait_timer import BusyWaitTimer
from lib.event.event import Event


class CustomEvent(Event):
    def __init__(self, name: str, number: int):
        super().__init__(name)
        self.number = number


class TestTimer(unittest.TestCase):
    def setUp(self):
        self.timer = BusyWaitTimer()
        self.firstEvent = CustomEvent("A", 1)
        self.secondEvent = CustomEvent("B", 2)
        self.thirdEvent = CustomEvent("C", 3)

    def tearDown(self):
        self.timer.stop()

    def testTimerInSingleThread(self):
        print("Test 1\n")
        q1, q2, q3 = Queue(), Queue(), Queue()
        self.timer.schedule(0.1, q1, self.firstEvent)
        self.timer.schedule(0.2, q2, self.secondEvent)
        self.timer.schedule(0.3, q3, self.thirdEvent)

        self.assertEqual(q1.get(), self.firstEvent)
        self.assertEqual(q2.get(), self.secondEvent)
        self.assertEqual(q3.get(), self.thirdEvent)

    def testTimerInMultipleThreads(self):
        print("\nTest 2\n")
        q1, q2, q3 = Queue(), Queue(), Queue()

        def thread1():
            n1 = self.timer.getNotifier()
            self.timer.schedule(0.01, n1, self.firstEvent)
            q1.put(n1.get())

        def thread2():
            n2 = self.timer.getNotifier()
            self.timer.schedule(0.02, n2, self.secondEvent)
            q2.put(n2.get())

        def thread3():
            n3 = self.timer.getNotifier()
            self.timer.schedule(0.03, n3, self.thirdEvent)
            q3.put(n3.get())

        t1 = Thread(target=thread1)
        t2 = Thread(target=thread2)
        t3 = Thread(target=thread3)

        t1.start()
        t2.start()
        t3.start()

        t1.join()
        t2.join()
        t3.join()

        self.assertEqual(q1.get(), self.firstEvent)
        self.assertEqual(q2.get(), self.secondEvent)
        self.assertEqual(q3.get(), self.thirdEvent)

    def testCancel(self):
        print("\nTest 3\n")
        q2, q3 = Queue(), Queue()
        queues = []

        def thread1(queues):
            n1 = self.timer.getNotifier()
            self.timer.schedule(1, n1, self.firstEvent)
            time.sleep(0.4)
            self.timer.cancel(self.firstEvent.getName())
            queues.append(n1)

        def thread2():
            n2 = self.timer.getNotifier()
            self.timer.schedule(0.02, n2, self.secondEvent)
            q2.put(n2.get())

        def thread3():
            n3 = self.timer.getNotifier()
            self.timer.schedule(0.03, n3, self.thirdEvent)
            q3.put(n3.get())

        t1 = Thread(target=thread1, args=(queues,))
        t2 = Thread(target=thread2)
        t3 = Thread(target=thread3)

        t1.start()
        t2.start()
        t3.start()

        t1.join()
        t2.join()
        t3.join()

        self.assertTrue(queues[0].empty())
        self.assertEqual(q2.get(), self.secondEvent)
        self.assertEqual(q3.get(), self.thirdEvent)


if __name__ == '__main__':
    unittest.main()
