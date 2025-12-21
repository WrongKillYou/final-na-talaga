import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_monitor.settings')
django.setup()

from users.models import User, Teacher, Parent, Child
from monitoring.models import Class, Enrollment, GradingScheme, GradeItem, FinalGrade

# ========================================
# 1. Create Teacher
# ========================================
teacher_user = User.objects.create_user(
    username='teacher1',
    password='teacher123',
    email='teacher@school.com',
    first_name='John',
    last_name='Doe',
    role='teacher'
)
teacher = Teacher.objects.create(
    user=teacher_user,
    license_number='LIC-2024-001',
    department='Mathematics',
    contact_number='09123456789'
)
print("✅ Teacher created: teacher1 / teacher123")

# ========================================
# 2. Create Parent
# ========================================
parent_user = User.objects.create_user(
    username='parent1',
    password='parent123',
    email='parent@email.com',
    first_name='Mary',
    last_name='Smith',
    role='parent'
)
parent = Parent.objects.create(
    user=parent_user,
    parent_email='mary@email.com',
    parent_contact='09198765432',
    relationship_to_child='Mother'
)
print("✅ Parent created: parent1 / parent123")

# ========================================
# 3. Create Children
# ========================================
child1 = Child.objects.create(
    lrn='123456789012',
    first_name='Alice',
    middle_name='Joy',
    last_name='Smith',
    gender='female',
    date_of_birth=date(2012, 3, 15),
    grade_level='grade_9',
    section='Sapphire',
    enrollment_date=date(2024, 6, 1),
    class_teacher=teacher
)
child1.parents.add(parent)

child2 = Child.objects.create(
    lrn='123456789013',
    first_name='Bob',
    middle_name='Ray',
    last_name='Smith',
    gender='male',
    date_of_birth=date(2014, 7, 20),
    grade_level='grade_7',
    section='Diamond',
    enrollment_date=date(2024, 6, 1),
    class_teacher=teacher
)
child2.parents.add(parent)
print(f"✅ Children created: {child1.get_full_name()}, {child2.get_full_name()}")

# ========================================
# 4. Create Classes
# ========================================
math_class = Class.objects.create(
    class_name='9-Sapphire Mathematics',
    subject='Mathematics',
    teacher=teacher
)

# Create grading scheme
GradingScheme.objects.create(
    class_obj=math_class,
    written_work_weight=0.4,
    performance_task_weight=0.4,
    quarterly_assessment_weight=0.2
)

# Enroll Alice
Enrollment.objects.create(student=child1, class_obj=math_class)
print(f"✅ Class created: {math_class}")

# ========================================
# 5. Add Sample Grades (Quarter 1)
# ========================================
# Written Work
GradeItem.objects.create(
    student=child1,
    class_obj=math_class,
    component='WW',
    score=45,
    highest_possible_score=50,
    quarter=1
)
GradeItem.objects.create(
    student=child1,
    class_obj=math_class,
    component='WW',
    score=38,
    highest_possible_score=40,
    quarter=1
)

# Performance Task
GradeItem.objects.create(
    student=child1,
    class_obj=math_class,
    component='PT',
    score=85,
    highest_possible_score=100,
    quarter=1
)

# Quarterly Assessment
GradeItem.objects.create(
    student=child1,
    class_obj=math_class,
    component='QA',
    score=42,
    highest_possible_score=50,
    quarter=1
)

# Compute final grade
final_grade = FinalGrade.objects.create(
    student=child1,
    class_obj=math_class,
    quarter=1
)
final_grade.compute_final_grade()
print(f"✅ Grades added for Q1. Final Grade: {final_grade.final_grade}")

print("\n" + "="*60)
print("SAMPLE DATA LOADED SUCCESSFULLY!")
print("="*60)
print("\nLOGIN CREDENTIALS:")
print("-" * 60)
print("TEACHER:")
print("  URL: http://127.0.0.1:8000/users/teacher/login/")
print("  Username: teacher1")
print("  Password: teacher123")
print("\nPARENT:")
print("  URL: http://127.0.0.1:8000/users/parent/login/")
print("  Username: parent1")
print("  Password: parent123")
print("\nADMIN:")
print("  URL: http://127.0.0.1:8000/admin/")
print("  Username: admin")
print("  Password: (what you set during createsuperuser)")
print("-" * 60)