# Create a dictionary
student = {
    "name": "Alice",
    "age": 20,
    "courses": ["Math", "Physics", "CS"],
    "gpa": 3.8
}

# Access values
print(student["name"])  # Alice
print(student.get("age"))  # 20

# Add/update
student["graduated"] = False
student["age"] = 21

# Iterate through dictionary
for key, value in student.items():
    print(f"{key}: {value}")

# Dictionary comprehension
squares = {x: x**2 for x in range(1, 6)}
# {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}