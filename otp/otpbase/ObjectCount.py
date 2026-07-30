from direct.showbase.Job import Job
import gc

class ObjectCount(Job):
    """ logs a count of the number of each type of object found in gc.get_objects() """
    def __init__(self, name, immediate=False, doneCallback=None):
        Job.__init__(self, name)
        self._doneCallback = doneCallback
        jobMgr.add(self)
        if immediate:
            jobMgr.finish(self)

    def destroy(self):
        self._doneCallback = None
        Job.destroy(self)

    def finished(self):
        if self._doneCallback:
            self._doneCallback(self)
        self.destroy()

    def run(self):
        objs = gc.get_objects()
        yield None
        type2count = {}
        for obj in objs:
            tn = safeTypeName(obj)
            type2count.setdefault(tn, 0)
            type2count[tn] += 1
            yield None
        # prevent garbage cycle
        del objs
        yield None
        count2type = invertDictLossless(type2count)
        yield None
        counts = list(count2type.keys())
        yield None
        counts.sort()
        yield None
        counts.reverse()
        yield None
        print('===== ObjectCount: \'%s\' =====' % (self.getJobName()))
        for count in counts:
            types = count2type[count]
            for type in types:
                print('%s: %s' % (count, type))
                yield None
        yield Job.Done
