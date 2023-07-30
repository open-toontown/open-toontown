""" 
"""

from direct.distributed.AsyncRequest import ASYNC_REQUEST_DEFAULT_TIMEOUT_IN_SECONDS, ASYNC_REQUEST_INFINITE_RETRIES, AsyncRequest
from direct.task import Task

from otp.uberdog.RejectCode import RejectCode


class ManagedAsyncRequest(AsyncRequest):
    """
    A ManagedAsyncRequest is different from an AsyncRequest in that it
    expects there to be a dclass method with the name specified in
    self.rejectString that takes one argument (such as an integer error
    code).  Also, it will send that message on timeout.

    The distObject passed in to the init is expected to have an asyncRequests
    member that is usable by the ManagedAsyncRequest.
    """
    @report(types = ['args'], dConfigParam = 'avatarmgr')
    def __init__(self, distObj, air, replyToChannelId=None,
                 timeoutTime=ASYNC_REQUEST_DEFAULT_TIMEOUT_IN_SECONDS,
                 key=None):
        assert self.notify.debugCall()
        self.distObj = distObj
        self.key = key
        if key is not None:
            req = distObj.asyncRequests.get(key)
            if req:
                req.delete()
            distObj.asyncRequests[key] = self
        AsyncRequest.__init__(self, air, replyToChannelId, timeoutTime,
                              ASYNC_REQUEST_INFINITE_RETRIES)

    def delete(self):
        if hasattr(self.distObj, "asyncRequests"):
            self.distObj.asyncRequests.pop(self.key, None)
        AsyncRequest.delete(self)

    def sendRejectCode(self, reasonId):
        assert self.notify.debugCall()
        if self.replyToChannelId:
            self.air.sendUpdateToChannel(self.distObj, self.replyToChannelId,
                                         self.rejectString, [reasonId])

    def timeout(self, task):
        if self.numRetries == ASYNC_REQUEST_INFINITE_RETRIES:
            return Task.again
        elif self.numRetries > 0:
            self.numRetries -= 1
            return Task.again
        else:
            self.sendRejectCode(RejectCode.TIMEOUT)
            AsyncRequest.timeout(self, task)
