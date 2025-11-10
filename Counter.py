

class Counter:

    counter = 0
    def __init__(self, counter):
        self.counter = counter
    def increment(self):
        self.counter += 1

a = Counter(12)
b = Counter(13)

print(f'a{a}')
print(f'b {b}')
print(a.counter)

a.increment()
b.increment()

print(a.counter)


