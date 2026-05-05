class List:
    def __init__(self):
        self.values = []

    def isEmpty(self):
        return len(self.values) == 0

    def insertSorted(self, value, sorting):
        i = 0
        while i < len(self.values):
            if sorting(self.values[i], value):
                break
            i += 1
        self.values.insert(i, value)

    def append(self, value):
        self.values.append(value)

    def get(self, index):
        if index < 0 or index >= len(self.values):
            raise IndexError("Index out of range")
        return self.values[index]

    def forEach(self, action):
        for value in self.values:
            action(value)

    def filter(self, filterFunction):
        self.values = [value for value in self.values if filterFunction(value)]

    def __str__(self):
        return str(self.values)
