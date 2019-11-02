

class ActivityBase:

    def __init__(self, activityId, x, y, h):
        self.activityId = activityId
        self.x = x
        self.y = y
        self.h = h

    def __str__(self):
        string = '<ActivityBase activityId=%d, ' % self.activityId
        string += 'x=%d, y=%d, h=%d>' % (self.x, self.y, self.h)
        return string

    def __repr__(self):
        return self.__str__()
