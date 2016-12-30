
import cmd
from queue import Queue
from threading import Thread


class Pub1(cmd.Cmd):
    intro = 'pub-sub example'
    prompt = '>>> '
    file = None

    def __init__(self, dispatch: Queue):
        super().__init__()
        self.dispatch = dispatch

    def do_f1(self, arg):
        self.dispatch.put(('f1', 'pub1 A'))

    def do_f2(self, arg):
        self.dispatch.put(('f2', 'pub1 B'))
        print ("do_f2 called....")

    def do_f3(self, arg):
        self.dispatch.put(('f3', 'pub1 C'))

    def do_allo(self, arg):
        print ("\nAllo!\n")

    def do_exit(self, arg):
        return True


def command_queue_fn(q: Queue):
    next = q.get()
    while next is not None:
        next[0](*(next[1:]))
        next = q.get()


def dispatcher_fn(dispatch: Queue, command: Queue, subscribers: list):
    next = dispatch.get()
    while next is not None:
        name = next[0]
        args = next[1:]
        for sub in subscribers:
            try:
                # command.put((getattr(sub, '%s' % name), *args))  Incompatible Python rev < 3.5
                command.put(([getattr(sub, str(name))] + list(args)))
                print (str(name))
            except AttributeError:
                pass
        next = dispatch.get()


class Sub1:

    def f1(self, msg):
        print('Sub1, f1 :', msg)

    def f2(self, msg):
        print('Sub1, f2 :', msg)


class Sub2:

    def f1(self, msg):
        print('Sub2, f2 :', msg)

    def f3(self, msg):
        print('Sub2, f3 :', msg)

if __name__ == '__main__':
    command_queue = Queue()
    dispatch_queue = Queue()
    pub1 = Pub1(dispatch_queue)
    sub1 = Sub1()
    sub2 = Sub2()

    thread_command_queue = Thread(target=command_queue_fn, name='cmd_queue', args=(command_queue,))
    thread_dispatcher = Thread(target=dispatcher_fn, name='dispath_queue', args=(dispatch_queue, command_queue, [sub1, sub2]))

    thread_command_queue.start()
    thread_dispatcher.start()

    pub1.cmdloop()

    dispatch_queue.put(None)
    command_queue.put(None)

    thread_command_queue.join()
    thread_dispatcher.join()
