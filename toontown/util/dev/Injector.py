import traceback

from direct.showbase.DirectObject import DirectObject


INJECTOR_KEY = 'f12'
INJECTOR_FILE = './toontown/util/dev/inject.py'


class DeveloperInjector(DirectObject):

    def start(self):
        print(f'Now listening for injector events. When {INJECTOR_KEY} is pressed all contents in {INJECTOR_FILE} are ran.')
        self.accept(INJECTOR_KEY, self.__inject)

    def stop(self):
        self.ignoreAll()

    def __inject(self):

        try:
            with open(INJECTOR_FILE, 'r'):
                pass
        except FileNotFoundError:
            print(f"File {INJECTOR_FILE} does not exist. Please create it and try again.")
            traceback.print_exc()
            return

        with open(INJECTOR_FILE, 'r') as f:
            code = f.read()
            try:
                exec(code, globals())
            except Exception as e:
                print(f"Exception thrown while injecting: {e}")
                traceback.print_exc()
                return
