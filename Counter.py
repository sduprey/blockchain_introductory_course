
class A:
    age = None
    def __init__(self, age):
        self.my_age = age
    def get_older(self):
        self.my_age += 1

a = A(12)
print(a)
print(a.my_age)
a.get_older()
