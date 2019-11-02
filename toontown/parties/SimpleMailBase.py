

class SimpleMailBase:

    def __init__(self, msgId, senderId, year, month, day, body):
        self.msgId = msgId
        self.senderId = senderId
        self.year = year
        self.month = month
        self.day = day
        self.body = body

    def __str__(self):
        string = 'msgId=%d ' % self.msgId
        string += 'senderId=%d ' % self.senderId
        string += 'sent=%s-%s-%s ' % (self.year, self.month, self.day)
        string += 'body=%s' % self.body
        return string
