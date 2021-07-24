from config import best_courses
best_courses = 0

def main():
    global best_courses
    best_courses += 1

def main1():
    global best_courses
    best_courses += 1


for i in range(3):
    main()
    main1()
print(best_courses)